from django.contrib import admin

from .models import ContatoImovel, SolicitacaoVisita


@admin.register(ContatoImovel)
class ContatoImovelAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'imovel', 'criado_em']
    search_fields = ['nome', 'email', 'mensagem']
    readonly_fields = ['criado_em']


@admin.register(SolicitacaoVisita)
class SolicitacaoVisitaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'imovel', 'data', 'horario']
    list_filter = ['data']
    search_fields = ['nome', 'email']
    readonly_fields = ['criado_em']
