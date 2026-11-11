from .models import ConfiguracaoSite, ContatoImovel, DadosPainel, PerfilCadastro


def avatar_usuario(user):
    """Dados do avatar da barra de navegação: versão da foto (se houver) e inicial do nome."""
    if not user.is_authenticated:
        return {}
    foto_em = (DadosPainel.objects.filter(usuario=user)
               .values_list('foto_atualizada_em', flat=True).first())
    nome = (PerfilCadastro.objects.filter(usuario=user).values_list('nome', flat=True).first()
            or user.get_full_name() or user.username or user.email or '?')
    return {
        'avatar_foto_versao': int(foto_em.timestamp()) if foto_em else None,
        'avatar_inicial': nome.strip()[:1].upper() or '?',
    }


def configuracao_site(request):
    configuracao = ConfiguracaoSite.objects.first()
    contexto = {
        'configuracao_site': configuracao,
        'admin_pending_questions': 0,
        'admin_recent_questions': [],
        **avatar_usuario(request.user),
    }
    if request.user.is_authenticated and request.user.is_staff:
        pendentes = ContatoImovel.objects.filter(
            status=ContatoImovel.Status.PENDENTE,
        )
        contexto['admin_pending_questions'] = pendentes.count()
        contexto['admin_recent_questions'] = pendentes[:3]
    return contexto
