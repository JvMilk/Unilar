from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import ContatoImovelForm, DuvidaForm, SolicitacaoVisitaForm
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import CadastroForm
from .models import ContatoImovel, Favorito, Imovel, PerfilCadastro
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login as entrar
from django.db import IntegrityError, transaction
from django.conf import settings
from django.http import Http404


IMOVEL = 'kitnet-no-centro'


def slugs_favoritos(request):
    """Favoritos de quem está logado vêm do banco; de visitantes, da sessão do navegador."""
    if request.user.is_authenticated:
        return list(Favorito.objects.filter(usuario=request.user).values_list('imovel__slug', flat=True))
    return request.session.get('favoritos', [])


def alternar_favorito(request, imovel):
    """Marca ou desmarca o favorito e devolve True se ele ficou marcado."""
    if request.user.is_authenticated:
        favorito, criado = Favorito.objects.get_or_create(usuario=request.user, imovel=imovel)
        if not criado:
            favorito.delete()
        return criado
    salvos = request.session.get('favoritos', [])
    if imovel.slug in salvos:
        salvos.remove(imovel.slug)
    else:
        salvos.append(imovel.slug)
    request.session['favoritos'] = salvos
    return imovel.slug in salvos

def login(request):
    if request.method == 'POST':
        usuario = authenticate(request, username=request.POST.get('email', '').strip().lower(),
                               password=request.POST.get('senha', ''))
        if usuario is not None:
            entrar(request, usuario)
            request.session.set_expiry(None if request.POST.get('lembrar') else 0)
            destino = request.POST.get('next') or request.GET.get('next')
            if destino and url_has_allowed_host_and_scheme(
                    destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(destino)  # volta para a página que pediu o login (ex.: Dúvidas)
            return redirect('admin_dashboard' if usuario.is_staff else 'inicio')
        messages.error(request, 'E-mail ou senha incorretos.')
    return render(request, 'login.html', {'google_login_ativo': settings.GOOGLE_LOGIN_ATIVO})


def login_bloqueado(request, *args, **kwargs):
    """Resposta mostrada quando o django-axes bloqueia o login por excesso de tentativas."""
    messages.error(request, 'Muitas tentativas de login com senha errada. Aguarde 15 minutos e tente novamente.')
    return render(request, 'login.html', {'google_login_ativo': settings.GOOGLE_LOGIN_ATIVO}, status=429)


def cadastro(request):
    form = CadastroForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        dados = form.cleaned_data
        try:
            with transaction.atomic():
                usuario = get_user_model().objects.create_user(
                    username=dados['email'], email=dados['email'], password=dados['senha'])
                PerfilCadastro.objects.create(usuario=usuario, nome=dados['nome'], cpf=dados['cpf'],
                                              endereco=dados['endereco'], cidade=dados['cidade'])
        except IntegrityError:
            form.add_error(None, 'Já existe um cadastro com este e-mail ou CPF.')
        else:
            messages.success(request, 'Conta criada! Entre com seu e-mail e senha.')
            return redirect('login')
    return render(request, 'cadastro.html', {'form': form})


def imoveis(request):
    return catalogo(request, template="lista_imoveis.html")


def inicio(request):
    return catalogo(request, titulo='Imóveis em destaque')


def sobre(request):
    """Página Sobre: números vêm do banco, nada é inventado."""
    disponiveis = Imovel.objects.filter(status=Imovel.Status.DISPONIVEL)
    return render(request, 'sobre.html', {
        'total_imoveis': disponiveis.count(),
        'total_cidades': disponiveis.values('cidade').distinct().count(),
        'total_tipos': len(Imovel.Tipo.choices),
        'cidades': sorted({c.split(' - ')[0] for c in disponiveis.values_list('cidade', flat=True)}),
        'destaques': [dados_catalogo(item) for item in disponiveis.prefetch_related('fotos')[:3]],
    })


def catalogo(request, titulo='Imóveis', somente_favoritos=False, template='inicio.html'):
    cidade = request.GET.get('cidade', '')
    tipo = request.GET.get('tipo', '')
    preco = request.GET.get('preco', '')
    salvos = slugs_favoritos(request)
    busca = request.GET.get('q', '').strip()
    bairro = request.GET.get('bairro', '')
    ordenar = request.GET.get('ordem', '')
    limite = request.GET.get('maximo', '')
    tetos = ('1200', '1800', '2500', '3500')
    bairros = Imovel.objects.filter(
        status=Imovel.Status.DISPONIVEL,
    ).exclude(bairro='').values_list('bairro', flat=True).distinct().order_by('bairro')
    resultado = []
    for registro in Imovel.objects.filter(status=Imovel.Status.DISPONIVEL).prefetch_related('fotos'):
        item = dados_catalogo(registro, salvos)
        if titulo == 'Imóveis em destaque' and item.get('destaque'):
            continue
        if bairro and bairro != item.get('bairro'):
            continue
        if busca.casefold() not in ' '.join(item.get(k, '') for k in ('titulo', 'cidade', 'bairro', 'tipo')).casefold():
            continue
        if limite in tetos and item['preco'] > int(limite):
            continue
        if cidade and item['cidade'] != cidade:
            continue
        if tipo and item['tipo'] != tipo and not (tipo == 'casa' and item['tipo'].startswith('casa')):
            continue
        valor = item['preco']
        if (preco == 'ate-800' and valor > 800 or
                preco == '800-1200' and not 800 <= valor <= 1200 or
                preco == 'acima-1200' and valor <= 1200):
            continue
        if somente_favoritos and item['slug'] not in salvos:
            continue
        resultado.append({**item, 'favorito': item['slug'] in salvos})
    if ordenar in ('low', 'high'):
        resultado.sort(key=lambda item: item['preco'], reverse=ordenar == 'high')
    return render(request, template, {
        'q': busca, 'bairro': bairro, 'bairros': bairros, 'ordem': ordenar,
        'maximo': limite, 'tetos': tetos,
        'titulo': titulo, 'imoveis': resultado, 'cidade': cidade,
        'tipo': tipo, 'tipos': Imovel.Tipo.choices, 'preco': preco,
        'cidades': Imovel.objects.filter(
            status=Imovel.Status.DISPONIVEL,
        ).values_list('cidade', flat=True).distinct().order_by('cidade'),
        'favorito': IMOVEL in salvos,
    })


def dados_catalogo(imovel, salvos=None):
    foto = next(iter(imovel.fotos.all()), None)
    if imovel.imagem_padrao:
        imagem = imovel.imagem_padrao
    elif foto:
        imagem = ''
    else:
        imagem = 'imagens/imovel-1.jpg'
    return {
        'slug': imovel.slug,
        'bairro': imovel.bairro,
        'tipo': imovel.tipo,
        'cidade': imovel.cidade,
        'preco': imovel.preco,
        'titulo': imovel.titulo,
        'imagem': imagem,
        'imagem_url': foto.imagem.url if foto else '',
        'detalhes': (
            f'{imovel.quartos} quarto(s) · {imovel.banheiros} banheiro(s) · '
            f'{imovel.area} m²'
        ),
        'descricao': imovel.descricao,
        'destaque': imovel.destaque,
        'etiqueta': imovel.destaque or imovel.get_tipo_display(),
        'favorito': imovel.slug in (salvos or []),
    }


def formatar_reais(valor):
    return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def contexto_detalhe(request, imovel):
    """Organiza os dados do cadastro no padrão da página de detalhes (igual para todos os imóveis)."""
    fotos = [foto.imagem.url for foto in imovel.fotos.all()]
    if not fotos:
        fotos = [static(imovel.imagem_padrao or 'imagens/imovel-1.jpg')]
    mesma_cidade = Imovel.objects.filter(status=Imovel.Status.DISPONIVEL, cidade=imovel.cidade)
    media = mesma_cidade.aggregate(media=Avg('preco'))['media'] if mesma_cidade.count() >= 3 else None
    anunciante = None
    if imovel.proprietario:
        perfil = PerfilCadastro.objects.filter(usuario=imovel.proprietario).first()
        anunciante = {
            'nome': (perfil.nome if perfil else imovel.proprietario.get_full_name()) or 'Equipe UniLar',
            'desde': imovel.proprietario.date_joined.year,
        }
    descricao = imovel.descricao.strip()
    endereco = f'{imovel.endereco}, {imovel.bairro}, {imovel.cidade}'
    return {
        'imovel': imovel,
        'fotos': fotos,
        'favorito': imovel.slug in slugs_favoritos(request),
        'resumo': imovel.resumo_espaco(),
        'destaques': imovel.destaques(),
        'comodidades': imovel.lista_comodidades(),
        'contas': imovel.contas_inclusas(),
        'preco_formatado': formatar_reais(imovel.preco),
        'abaixo_da_media': media is not None and imovel.preco < media,
        'anunciante': anunciante or {'nome': 'Equipe UniLar', 'desde': None},
        'descricao_longa': len(descricao) > 360 or descricao.count('\n') > 5,
        'mapa_url': 'https://www.google.com/maps/search/?api=1&query=' + quote_plus(endereco),
        'endereco_completo': endereco,
        'maps_key': settings.GOOGLE_MAPS_API_KEY,
        # Pontos de referência pesquisados ao redor do endereço (botões ao lado do mapa).
        'pontos_referencia': [
            ('O imóvel', 'bi-house-door', ''),
            ('Universidades', 'bi-mortarboard', 'universidade'),
            ('Mercados', 'bi-cart3', 'supermercado'),
            ('Farmácias', 'bi-capsule', 'farmácia'),
            ('Restaurantes', 'bi-cup-straw', 'restaurante'),
            ('Ponto de ônibus', 'bi-bus-front', 'ponto de ônibus'),
            ('Academias', 'bi-bicycle', 'academia'),
        ],
    }


def imovel_publico(request, slug):
    imovel = get_object_or_404(
        Imovel.objects.prefetch_related('fotos').select_related('proprietario'),
        slug=slug,
        status=Imovel.Status.DISPONIVEL,
    )
    request.session['visitados'] = list(dict.fromkeys(
        request.session.get('visitados', []) + [slug]
    ))
    return render(request, 'imovel_publico.html', contexto_detalhe(request, imovel))


@require_POST
def contato_imovel_publico(request, slug):
    imovel = get_object_or_404(Imovel, slug=slug, status=Imovel.Status.DISPONIVEL)
    form = ContatoImovelForm(request.POST)
    if not form.is_valid():
        return render(request, 'imovel_publico.html', {**contexto_detalhe(request, imovel), 'form': form},
                      status=400)
    contato = form.save(commit=False)
    contato.imovel = slug
    contato.save()
    messages.success(request, 'Sua dúvida foi enviada. A equipe UniLar responderá em breve.')
    return redirect('imovel_publico', slug=slug)


def duvidas(request):
    """Página Dúvidas: qualquer pessoa vê; só quem está logado envia a pergunta."""
    imoveis = Imovel.objects.filter(status=Imovel.Status.DISPONIVEL).prefetch_related('fotos')
    form = DuvidaForm(request.POST if request.method == 'POST' else None)
    imovel_aberto = None
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Entre na sua conta para enviar sua dúvida.')
            return redirect(f"{reverse('login')}?next={reverse('duvidas')}")
        imovel = imoveis.filter(slug=request.POST.get('imovel', '')).first()
        if form.is_valid() and imovel:
            perfil = PerfilCadastro.objects.filter(usuario=request.user).first()
            duvida = form.save(commit=False)
            duvida.imovel = imovel.slug
            duvida.usuario = request.user
            duvida.email = request.user.email
            duvida.nome = (perfil.nome if perfil else request.user.get_full_name()) or request.user.email
            duvida.save()
            destino = request.POST.get('next', '')
            if destino and url_has_allowed_host_and_scheme(
                    destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                messages.success(request, 'Dúvida enviada! A resposta aparece na página Dúvidas, em "Minhas dúvidas".')
                return redirect(destino)
            messages.success(request, f'Dúvida sobre "{imovel.titulo}" enviada! Você verá a resposta aqui nesta página.')
            return redirect('duvidas')
        if imovel is None:
            form.add_error(None, 'Escolha um imóvel da lista para enviar sua dúvida.')
        imovel_aberto = imovel
    lista_imoveis = [dados_catalogo(item) for item in imoveis]
    minhas_duvidas = []
    if request.user.is_authenticated:
        por_slug = {item['slug']: item for item in lista_imoveis}
        minhas_duvidas = list(ContatoImovel.objects.filter(usuario=request.user)[:5])
        for duvida in minhas_duvidas:
            duvida.imovel_dados = por_slug.get(duvida.imovel)  # None se o imóvel saiu do ar
            duvida.titulo_imovel = duvida.imovel_dados['titulo'] if duvida.imovel_dados else duvida.imovel
    return render(request, 'duvidas.html', {
        'imoveis': lista_imoveis,
        'form': form,
        'imovel_aberto': imovel_aberto,
        'minhas_duvidas': minhas_duvidas,
    }, status=400 if request.method == 'POST' else 200)


@require_POST
def favoritar_catalogo(request, slug):
    imovel = get_object_or_404(Imovel, slug=slug, status=Imovel.Status.DISPONIVEL)
    alternar_favorito(request, imovel)
    return redirect('favoritos')


def detalhe_imovel(request):
    imovel = get_object_or_404(
        Imovel.objects.prefetch_related('fotos'),
        slug=IMOVEL,
        status=Imovel.Status.DISPONIVEL,
    )
    visitados = request.session.get('visitados', [])
    if IMOVEL not in visitados:
        request.session['visitados'] = visitados + [IMOVEL]
    # Mesmo modelo de página de todos os outros imóveis.
    return render(request, 'imovel_publico.html', contexto_detalhe(request, imovel))


def favoritos(request):
    return catalogo(request, titulo='Meus favoritos', somente_favoritos=True)


@require_POST
def favoritar_imovel(request):
    imovel = get_object_or_404(Imovel, slug=IMOVEL)
    return JsonResponse({'favorito': alternar_favorito(request, imovel)})


@require_POST
def contato_imovel(request):
    form = ContatoImovelForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'erros': form.errors.get_json_data()}, status=400)
    contato = form.save(commit=False)
    contato.imovel = IMOVEL
    contato.save()
    return JsonResponse({'mensagem': 'Seu interesse foi registrado no UniLar. '
                         'O envio de e-mail ao proprietário ainda não está disponível.'}, status=201)


@require_POST
def solicitar_visita(request):
    form = SolicitacaoVisitaForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'erros': form.errors.get_json_data()}, status=400)
    visita = form.save(commit=False)
    visita.imovel = IMOVEL
    visita.save()
    return JsonResponse({'mensagem': 'Pedido de visita registrado para '
                         f'{visita.data:%d/%m/%Y}, às {visita.horario:%H:%M}. '
                         'A visita depende de confirmação do proprietário.'}, status=201)


from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import DadosPainel
from .forms import FotoPerfilForm, PerfilPainelForm
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Avg
from django.templatetags.static import static
from urllib.parse import quote_plus


@login_required(login_url='login')
def painel(request):
    perfil = PerfilCadastro.objects.filter(usuario=request.user).first()
    dados = DadosPainel.objects.filter(usuario=request.user).defer('foto').first()
    nome = (perfil.nome if perfil else request.user.get_full_name()) or request.user.username
    form = PerfilPainelForm(request.POST if request.method == 'POST' else None,
                           instance=dados, initial={'nome': nome})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            dados = form.save(commit=False)
            dados.usuario = request.user
            dados.save()
            request.user.first_name = form.cleaned_data['nome']
            request.user.last_name = ''
            request.user.save(update_fields=['first_name', 'last_name'])
            if perfil:
                perfil.nome = form.cleaned_data['nome']
                perfil.save(update_fields=['nome'])
        messages.success(request, 'Perfil atualizado.')
        return redirect('painel')
    salvos = slugs_favoritos(request)
    visitados = request.session.get('visitados', [])
    favoritos = (Favorito.objects.filter(usuario=request.user, imovel__status=Imovel.Status.DISPONIVEL)
                 .select_related('imovel').prefetch_related('imovel__fotos'))
    return render(request, 'painel.html', {
        'nome': nome, 'dados': dados, 'form': form, 'perfil': perfil,
        # CPF parcialmente escondido na tela: ***.982.247-**
        'cpf_mascarado': f'***.{perfil.cpf[3:6]}.{perfil.cpf[6:9]}-**' if perfil and len(perfil.cpf) == 11 else '',
        'editando': request.method == 'POST' or request.GET.get('editar') == '1',
        'salvos': [dados_catalogo(favorito.imovel, salvos) for favorito in favoritos],
        'visitados': [
            dados_catalogo(item, salvos)
            for item in Imovel.objects.filter(slug__in=visitados, status=Imovel.Status.DISPONIVEL).prefetch_related('fotos')
        ],
    })


@login_required(login_url='login')
@require_POST
def painel_foto_enviar(request):
    form = FotoPerfilForm(request.POST, request.FILES)
    if form.is_valid():
        dados, _ = DadosPainel.objects.get_or_create(usuario=request.user)
        dados.foto = form.cleaned_data['foto']
        dados.foto_atualizada_em = timezone.now()
        dados.save(update_fields=['foto', 'foto_atualizada_em'])
        messages.success(request, 'Foto de perfil atualizada.')
    else:
        messages.error(request, form.errors['foto'][0])
    return redirect('painel')


@login_required(login_url='login')
@require_POST
def painel_foto_remover(request):
    DadosPainel.objects.filter(usuario=request.user).update(foto=None, foto_atualizada_em=None)
    messages.success(request, 'Foto de perfil removida.')
    return redirect('painel')


@login_required(login_url='login')
def painel_foto(request):
    """Entrega a foto de quem está logado (cada usuário só acessa a própria)."""
    dados = DadosPainel.objects.filter(usuario=request.user).only('foto').first()
    if not dados or not dados.foto:
        raise Http404
    resposta = HttpResponse(bytes(dados.foto), content_type='image/jpeg')
    resposta['Cache-Control'] = 'private, max-age=86400'
    return resposta


@require_POST
def sair(request):
    logout(request)
    return redirect('inicio')
