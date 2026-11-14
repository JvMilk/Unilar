import smtplib
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AdminConfiguracaoForm, AdminImovelForm
from .middleware import FUSO_RELATORIOS
from .models import (
    AcessoDiario, AluguelConfirmado, ConfiguracaoSite, ContatoImovel, DadosPainel,
    FotoImovel, Imovel, PerfilCadastro, SolicitacaoVisita,
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
    hoje = timezone.localdate(timezone=FUSO_RELATORIOS)
    periodos = (3, 6, 12)
    quantidade = next((periodo for periodo in periodos if str(periodo) == request.GET.get('meses')), 12)
    meses = []
    for offset in range(quantidade - 1, -1, -1):
        indice_mes = hoje.year * 12 + hoje.month - 1 - offset
        meses.append(date(indice_mes // 12, indice_mes % 12 + 1, 1))

    inicio = datetime.combine(meses[0], time.min, tzinfo=FUSO_RELATORIOS)
    fim = datetime.combine(hoje + timedelta(days=1), time.min, tzinfo=FUSO_RELATORIOS)

    def dados_mensais(queryset, campo='criado_em'):
        linhas = (
            queryset.filter(**{f'{campo}__gte': inicio, f'{campo}__lt': fim})
            .annotate(mes=TruncMonth(campo, tzinfo=FUSO_RELATORIOS))
            .values('mes').annotate(total=Count('id')).order_by('mes')
        )
        return {linha['mes'].date().replace(day=1): linha['total'] for linha in linhas}

    acessos_por_mes = {
        linha['mes']: linha['total']
        for linha in AcessoDiario.objects.filter(dia__range=(meses[0], hoje))
        .annotate(mes=TruncMonth('dia')).values('mes').annotate(total=Sum('visualizacoes')).order_by('mes')
    }
    primeiro_acesso = AcessoDiario.objects.filter(dia__lte=hoje).order_by('dia').values_list('dia', flat=True).first()
    series = {
        'imoveis': dados_mensais(Imovel.objects.all()),
        'duvidas': dados_mensais(ContatoImovel.objects.all()),
        'usuarios': dados_mensais(get_user_model().objects.all(), 'date_joined'),
        'visitas': dados_mensais(SolicitacaoVisita.objects.all()),
        'alugueis': dados_mensais(AluguelConfirmado.objects.all(), 'registrado_em'),
    }
    relatorio = []
    for mes in meses:
        linha = {nome: dados.get(mes, 0) for nome, dados in series.items()}
        linha['mes'] = mes
        linha['acessos'] = (
            acessos_por_mes.get(mes, 0)
            if primeiro_acesso and mes >= primeiro_acesso.replace(day=1) else None
        )
        relatorio.append(linha)

    status_totais = {
        linha['status']: linha['total']
        for linha in Imovel.objects.values('status').annotate(total=Count('pk')).order_by()
    }
    total_imoveis = sum(status_totais.values())
    situacao = [{
        'nome': label,
        'status': status,
        'total': status_totais.get(status, 0),
        'percentual': round(status_totais.get(status, 0) * 100 / total_imoveis) if total_imoveis else 0,
    } for status, label in Imovel.Status.choices]
    return render(request, 'admin/relatorios.html', {
        'relatorio': relatorio,
        'mes_atual': relatorio[-1],
        'primeiro_acesso': primeiro_acesso,
        'periodos': periodos,
        'quantidade': quantidade,
        'situacao': situacao,
        'total_imoveis': total_imoveis,
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
    if request.method == 'POST':
        with transaction.atomic():
            imovel = get_object_or_404(Imovel.objects.select_for_update(), pk=pk) if pk else None
            form = AdminImovelForm(request.POST, request.FILES, instance=imovel)
            if not form.is_valid():
                return render(request, 'admin/imovel_form.html', {
                    'form': form, 'imovel': imovel, 'fotos': imovel.fotos.all() if imovel else [],
                })
            imovel = form.save()
            if form.cleaned_data['aluguel_confirmado']:
                AluguelConfirmado.objects.create(imovel=imovel)
            for foto in form.cleaned_data['fotos']:
                FotoImovel.objects.create(imovel=imovel, imagem=foto)
            ids_excluidos = request.POST.getlist('excluir_fotos')
            if ids_excluidos:
                imovel.fotos.filter(pk__in=ids_excluidos).delete()
        messages.success(request, 'Imóvel salvo com sucesso.')
        return redirect('admin_imoveis')
    imovel = get_object_or_404(Imovel, pk=pk) if pk else None
    form = AdminImovelForm(instance=imovel)
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
        duvidas = duvidas.filter(nome__icontains=busca) | duvidas.filter(email__icontains=busca) | duvidas.filter(mensagem__icontains=busca) | duvidas.filter(assunto__icontains=busca)
    if status in ContatoImovel.Status.values:
        duvidas = duvidas.filter(status=status)
    selecionada = get_object_or_404(ContatoImovel, pk=pk) if pk else duvidas.first()
    if pk:
        duvidas = ContatoImovel.objects.all()
    imovel_selecionado = Imovel.objects.filter(slug=selecionada.imovel).first() if selecionada else None
    return render(request, 'admin/mensagens.html', {
        'duvidas': duvidas,
        'selecionada': selecionada,
        'imovel_selecionado': imovel_selecionado,
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
