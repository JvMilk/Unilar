import logging
from zoneinfo import ZoneInfo

from django.db import DatabaseError
from django.db.models import F
from django.utils import timezone

from .models import AcessoDiario


logger = logging.getLogger(__name__)
FUSO_RELATORIOS = ZoneInfo('America/Sao_Paulo')
PAGINAS_PUBLICAS = {'home', 'inicio', 'imoveis', 'imovel_publico', 'detalhe_imovel', 'sobre', 'duvidas'}


def contar_acessos_publicos(get_response):
    def middleware(request):
        response = get_response(request)
        rota = request.resolver_match
        if request.method == 'GET' and response.status_code == 200 and rota and rota.url_name in PAGINAS_PUBLICAS:
            try:
                acesso, criado = AcessoDiario.objects.get_or_create(
                    dia=timezone.localdate(timezone=FUSO_RELATORIOS), defaults={'visualizacoes': 1},
                )
                if not criado:
                    AcessoDiario.objects.filter(pk=acesso.pk).update(visualizacoes=F('visualizacoes') + 1)
            except DatabaseError:
                logger.exception('Falha ao registrar visualização de página pública.')
        return response

    return middleware
