from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import ContatoImovelForm, SolicitacaoVisitaForm
from .catalogo import IMOVEIS
from django.http import Http404


IMOVEL = 'kitnet-no-centro'

def login(request):
    return render(request, 'login.html')


def imoveis(request):
    return catalogo(request)


def inicio(request):
    return catalogo(request, titulo='Imóveis em destaque')


def catalogo(request, titulo='Imóveis', somente_favoritos=False):
    cidade = request.GET.get('cidade', '')
    tipo = request.GET.get('tipo', '')
    preco = request.GET.get('preco', '')
    salvos = request.session.get('favoritos', [])
    resultado = []
    for item in IMOVEIS:
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
    return render(request, 'inicio.html', {
        'titulo': titulo, 'imoveis': resultado, 'cidade': cidade,
        'tipo': tipo, 'preco': preco,
        'favorito': IMOVEL in salvos,
    })


@require_POST
def favoritar_catalogo(request, slug):
    if slug not in {item['slug'] for item in IMOVEIS}:
        raise Http404
    salvos = request.session.get('favoritos', [])
    if slug in salvos:
        salvos.remove(slug)
    else:
        salvos.append(slug)
    request.session['favoritos'] = salvos
    return redirect('favoritos')


def detalhe_imovel(request):
    return render(request, 'imovel.html', {
        'favorito': IMOVEL in request.session.get('favoritos', []),
    })


def favoritos(request):
    return catalogo(request, titulo='Meus favoritos', somente_favoritos=True)


@require_POST
def favoritar_imovel(request):
    favoritos = request.session.get('favoritos', [])
    if IMOVEL in favoritos:
        favoritos.remove(IMOVEL)
    else:
        favoritos.append(IMOVEL)
    request.session['favoritos'] = favoritos
    return JsonResponse({'favorito': IMOVEL in favoritos})


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
