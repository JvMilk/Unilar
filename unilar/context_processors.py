from .models import ConfiguracaoSite, ContatoImovel


def configuracao_site(request):
    configuracao = ConfiguracaoSite.objects.first()
    if request.user.is_authenticated and request.user.is_staff:
        pendentes = ContatoImovel.objects.filter(
            status=ContatoImovel.Status.PENDENTE,
        )
        return {
            'configuracao_site': configuracao,
            'admin_pending_questions': pendentes.count(),
            'admin_recent_questions': pendentes[:3],
        }
    return {
        'configuracao_site': configuracao,
        'admin_pending_questions': 0,
        'admin_recent_questions': [],
    }
