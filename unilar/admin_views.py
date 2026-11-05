import smtplib
from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AdminConfiguracaoForm, AdminImovelForm
from .models import (
    ConfiguracaoSite, ContatoImovel, DadosPainel, FotoImovel, Imovel,
    PerfilCadastro,
)


def administrador(user):
    return user.is_authenticated and user.is_staff


admin_required = user_passes_test(administrador, login_url='login')


@admin_required
def dashboard(request):
    hoje = timezone.localdate()
    periodos = {'7': 7, '30': 30, '90': 90}
    periodo = request.GET.get('periodo', '30')
    dias = periodos.get(periodo, 30)
    periodo = str(dias)
    inicio = hoje - timedelta(days=dias - 1)

    def dados_diarios(queryset):
        linhas = (
            queryset.filter(criado_em__date__gte=inicio, criado_em__date__lte=hoje)
            .annotate(dia=TruncDate('criado_em'))
            .values('dia').annotate(total=Count('id')).order_by('dia')
        )
        return {linha['dia']: linha['total'] for linha in linhas}

    registros_imoveis = dados_diarios(Imovel.objects.all())
    registros_duvidas = dados_diarios(ContatoImovel.objects.all())
    dias_grafico = [inicio + timedelta(days=offset) for offset in range(dias)]
    labels = [dia.strftime('%d/%m') for dia in dias_grafico]
    dados_imoveis = [registros_imoveis.get(dia, 0) for dia in dias_grafico]
    dados_duvidas = [registros_duvidas.get(dia, 0) for dia in dias_grafico]
    recentes = (
        Imovel.objects.select_related('proprietario')
        .prefetch_related('fotos').order_by('-criado_em', 'pk')[:3]
    )
    ultimas_duvidas = list(ContatoImovel.objects.order_by('-criado_em', 'pk')[:5])
    for duvida in ultimas_duvidas:
        duvida.iniciais = ''.join(parte[0] for parte in duvida.nome.split()[:2]).upper()
    pendentes = ContatoImovel.objects.filter(status=ContatoImovel.Status.PENDENTE).count()
    return render(request, 'admin/dashboard.html', {
        'total_imoveis': Imovel.objects.count(),
        'disponiveis': Imovel.objects.filter(status=Imovel.Status.DISPONIVEL).count(),
        'alugados': Imovel.objects.filter(status=Imovel.Status.ALUGADO).count(),
        'duvidas_pendentes': pendentes,
        'recentes': recentes,
        'ultimas_duvidas': ultimas_duvidas,
        'periodo': periodo,
        'periodo_label': f'Últimos {dias} dias',
        'chart_labels': labels,
        'chart_data': dados_imoveis,
        'chart_questions': dados_duvidas,
    })


@admin_required
def relatorios_admin(request):
    hoje = timezone.localdate()
    meses = []
    for offset in range(11, -1, -1):
        indice_mes = hoje.year * 12 + hoje.month - 1 - offset
        meses.append(date(indice_mes // 12, indice_mes % 12 + 1, 1))

    def dados_mensais(queryset):
        linhas = (
            queryset.filter(criado_em__date__gte=meses[0])
            .annotate(mes=TruncMonth('criado_em'))
            .values('mes').annotate(total=Count('id')).order_by('mes')
        )
        return {linha['mes'].date().replace(day=1): linha['total'] for linha in linhas}

    imoveis_por_mes = dados_mensais(Imovel.objects.all())
    duvidas_por_mes = dados_mensais(ContatoImovel.objects.all())
    relatorio = [{
        'mes': mes,
        'imoveis': imoveis_por_mes.get(mes, 0),
        'duvidas': duvidas_por_mes.get(mes, 0),
    } for mes in meses]
    return render(request, 'admin/relatorios.html', {
        'relatorio': relatorio,
        'total_imoveis': Imovel.objects.count(),
        'total_duvidas': ContatoImovel.objects.count(),
        'total_usuarios': get_user_model().objects.count(),
        'disponiveis': Imovel.objects.filter(status=Imovel.Status.DISPONIVEL).count(),
    })


@admin_required
def imoveis_admin(request):
    imoveis = Imovel.objects.select_related('proprietario').prefetch_related('fotos')
    busca = request.GET.get('q', '').strip()
    categoria = request.GET.get('tipo', '')
    status = request.GET.get('status', '')
    if busca:
        imoveis = imoveis.filter(titulo__icontains=busca) | imoveis.filter(endereco__icontains=busca)
    if categoria in Imovel.Tipo.values:
        imoveis = imoveis.filter(tipo=categoria)
    if status in Imovel.Status.values:
        imoveis = imoveis.filter(status=status)
    return render(request, 'admin/imoveis.html', {
        'imoveis': imoveis,
        'q': busca,
        'tipo_selecionado': categoria,
        'status_selecionado': status,
        'tipos': Imovel.Tipo.choices,
        'status_choices': Imovel.Status.choices,
    })


@admin_required
def imovel_form(request, pk=None):
    imovel = get_object_or_404(Imovel, pk=pk) if pk else None
    form = AdminImovelForm(
        request.POST or None,
        request.FILES or None,
        instance=imovel,
    )
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            imovel = form.save()
            for foto in form.cleaned_data['fotos']:
                FotoImovel.objects.create(imovel=imovel, imagem=foto)
            ids_excluidos = request.POST.getlist('excluir_fotos')
            if ids_excluidos:
                imovel.fotos.filter(pk__in=ids_excluidos).delete()
        messages.success(request, 'Imóvel salvo com sucesso.')
        return redirect('admin_imoveis')
    return render(request, 'admin/imovel_form.html', {
        'form': form,
        'imovel': imovel,
        'fotos': imovel.fotos.all() if imovel else [],
    })


@admin_required
@require_POST
def excluir_imovel(request, pk):
    imovel = get_object_or_404(Imovel, pk=pk)
    imovel.delete()
    messages.success(request, 'Imóvel excluído.')
    return redirect('admin_imoveis')


@admin_required
def anuncios_admin(request):
    anuncios = Imovel.objects.select_related('proprietario').all()
    busca = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if busca:
        anuncios = anuncios.filter(titulo__icontains=busca) | anuncios.filter(endereco__icontains=busca)
    if status in Imovel.Status.values:
        anuncios = anuncios.filter(status=status)
    return render(request, 'admin/anuncios.html', {
        'anuncios': anuncios,
        'q': busca,
        'status_selecionado': status,
        'status_choices': Imovel.Status.choices,
    })


@admin_required
@require_POST
def atualizar_anuncio(request, pk):
    anuncio = get_object_or_404(Imovel, pk=pk)
    status = request.POST.get('status')
    if status not in Imovel.Status.values:
        messages.error(request, 'Selecione um status válido.')
    else:
        anuncio.status = status
        anuncio.save(update_fields=['status', 'atualizado_em'])
        messages.success(request, 'Status do anúncio atualizado.')
    return redirect('admin_anuncios')


@admin_required
def mensagens_admin(request, pk=None):
    duvidas = ContatoImovel.objects.all()
    busca = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if busca:
        duvidas = duvidas.filter(nome__icontains=busca) | duvidas.filter(email__icontains=busca) | duvidas.filter(mensagem__icontains=busca)
    if status in ContatoImovel.Status.values:
        duvidas = duvidas.filter(status=status)
    selecionada = get_object_or_404(ContatoImovel, pk=pk) if pk else duvidas.first()
    if pk:
        duvidas = ContatoImovel.objects.all()
    return render(request, 'admin/mensagens.html', {
        'duvidas': duvidas,
        'selecionada': selecionada,
        'q': busca,
        'status_selecionado': status,
        'status_choices': ContatoImovel.Status.choices,
    })


@admin_required
@require_POST
def responder_mensagem(request, pk):
    duvida = get_object_or_404(ContatoImovel, pk=pk)
    resposta = request.POST.get('resposta', '').strip()
    acao = request.POST.get('acao')
    if acao == 'excluir':
        duvida.delete()
        messages.success(request, 'Mensagem excluída.')
    elif acao == 'pendente':
        duvida.status = ContatoImovel.Status.PENDENTE
        duvida.save(update_fields=['status'])
        messages.success(request, 'Mensagem marcada como pendente.')
    elif acao == 'responder' and resposta:
        duvida.resposta = resposta
        duvida.status = ContatoImovel.Status.RESPONDIDA
        duvida.respondido_em = timezone.now()
        duvida.save(update_fields=['resposta', 'status', 'respondido_em'])
        if settings.EMAIL_HOST and settings.DEFAULT_FROM_EMAIL:
            try:
                configuracao = ConfiguracaoSite.objects.first()
                nome_site = configuracao.nome_site if configuracao else 'UniLar'
                send_mail(
                    f'Resposta à sua mensagem — {nome_site}',
                    resposta,
                    settings.DEFAULT_FROM_EMAIL,
                    [duvida.email],
                    fail_silently=False,
                )
            except (OSError, smtplib.SMTPException):
                messages.error(request, 'A resposta foi salva, mas o envio do e-mail falhou.')
            else:
                messages.success(request, 'Resposta salva e enviada por e-mail.')
        else:
            messages.success(request, 'Resposta salva. O envio por e-mail não está configurado.')
    else:
        messages.error(request, 'Escreva uma resposta antes de enviar.')
    return redirect('admin_mensagens_detalhe', pk=pk) if acao != 'excluir' else redirect('admin_mensagens')


@admin_required
def usuarios_admin(request):
    usuarios = get_user_model().objects.select_related('perfilcadastro').order_by('-date_joined')
    busca = request.GET.get('q', '').strip()
    if busca:
        usuarios = (
            usuarios.filter(email__icontains=busca)
            | usuarios.filter(username__icontains=busca)
            | usuarios.filter(first_name__icontains=busca)
            | usuarios.filter(last_name__icontains=busca)
            | usuarios.filter(perfilcadastro__nome__icontains=busca)
        )
    selecionado = None
    perfil = None
    dados_painel = None
    anuncios = []
    user_id = request.GET.get('usuario')
    if user_id:
        selecionado = get_object_or_404(get_user_model(), pk=user_id)
        perfil = PerfilCadastro.objects.filter(usuario=selecionado).first()
        dados_painel = DadosPainel.objects.filter(usuario=selecionado).first()
        anuncios = selecionado.imoveis.all()
    return render(request, 'admin/usuarios.html', {
        'usuarios': usuarios,
        'q': busca,
        'selecionado': selecionado,
        'perfil': perfil,
        'dados_painel': dados_painel,
        'anuncios_usuario': anuncios,
    })


@admin_required
@require_POST
def atualizar_usuario(request, pk):
    usuario = get_object_or_404(get_user_model(), pk=pk)
    acao = request.POST.get('acao')
    if usuario == request.user or usuario.is_superuser:
        raise PermissionDenied
    if not request.user.is_superuser and (usuario.is_staff or acao == 'staff'):
        raise PermissionDenied
    if acao == 'ativo':
        usuario.is_active = not usuario.is_active
        usuario.save(update_fields=['is_active'])
        messages.success(request, 'Acesso do usuário atualizado.')
    elif acao == 'staff' and request.user.is_superuser:
        usuario.is_staff = not usuario.is_staff
        usuario.save(update_fields=['is_staff'])
        messages.success(request, 'Permissão administrativa atualizada.')
    else:
        messages.error(request, 'Operação inválida ou não autorizada.')
    return redirect(f'/administracao/usuarios/?usuario={usuario.pk}')


@admin_required
def configuracoes_admin(request):
    configuracao, _ = ConfiguracaoSite.objects.get_or_create(pk=1)
    form = AdminConfiguracaoForm(request.POST or None, instance=configuracao)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Configurações salvas.')
        return redirect('admin_configuracoes')
    return render(request, 'admin/configuracoes.html', {'form': form})
