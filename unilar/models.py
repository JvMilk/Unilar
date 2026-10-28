from django.db import models

class ContatoImovel(models.Model):
    imovel = models.SlugField(default='kitnet-no-centro')
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    mensagem = models.TextField(max_length=3000)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'contato de imóvel'
        verbose_name_plural = 'contatos de imóveis'

    def __str__(self):
        return f'{self.nome} — {self.imovel}'


class SolicitacaoVisita(models.Model):
    imovel = models.SlugField(default='kitnet-no-centro')
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    data = models.DateField()
    horario = models.TimeField()
    observacao = models.TextField(max_length=1000, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data', 'horario']
        verbose_name = 'solicitação de visita'
        verbose_name_plural = 'solicitações de visita'

    def __str__(self):
        return f'{self.nome} — {self.data:%d/%m/%Y} {self.horario:%H:%M}'
