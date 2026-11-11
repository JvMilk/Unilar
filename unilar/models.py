from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import slugify


class ContatoImovel(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        RESPONDIDA = 'respondida', 'Respondida'

    imovel = models.SlugField(default='kitnet-no-centro', max_length=180)
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    mensagem = models.TextField(max_length=3000)
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDENTE)
    resposta = models.TextField(blank=True)
    respondido_em = models.DateTimeField(null=True, blank=True)

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


class PerfilCadastro(models.Model):
    usuario = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=11, unique=True)
    endereco = models.CharField(max_length=200)
    cidade = models.CharField(max_length=100)


class DadosPainel(models.Model):
    usuario = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    telefone = models.CharField(max_length=25, blank=True)
    curso = models.CharField(max_length=150, blank=True)
    universidade = models.CharField(max_length=150, blank=True)
    # Foto de perfil guardada no próprio banco (JPEG 320x320, ~20-40 KB).
    # Na Vercel, arquivos gravados em pasta não permanecem entre implantações.
    foto = models.BinaryField(null=True, blank=True, editable=False)
    foto_atualizada_em = models.DateTimeField(null=True, blank=True, editable=False)


class Imovel(models.Model):
    class Tipo(models.TextChoices):
        APARTAMENTO = 'apartamento', 'Apartamento'
        KITNET = 'kitnet', 'Kitnet'
        CASA = 'casa', 'Casa'
        CASA_COMPARTILHADA = 'casa-compartilhada', 'Casa compartilhada'
        OUTRO = 'outro', 'Outro'

    class Status(models.TextChoices):
        DISPONIVEL = 'disponivel', 'Disponível'
        ALUGADO = 'alugado', 'Alugado'
        INATIVO = 'inativo', 'Inativo'
        PENDENTE = 'pendente', 'Pendente de aprovação'

    proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='imoveis',
    )
    titulo = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    descricao = models.TextField()
    preco = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
    )
    endereco = models.CharField(max_length=220)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=120)
    quartos = models.PositiveSmallIntegerField(default=0)
    banheiros = models.PositiveSmallIntegerField(default=0)
    vagas = models.PositiveSmallIntegerField(default=0)
    area = models.PositiveIntegerField(
        help_text='Área em metros quadrados', validators=[MinValueValidator(1)],
    )
    tipo = models.CharField(max_length=24, choices=Tipo.choices)
    informacoes_adicionais = models.TextField(blank=True)
    imagem_padrao = models.CharField(max_length=180, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DISPONIVEL)
    destaque = models.CharField(max_length=40, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em', 'pk']
        verbose_name = 'imóvel'
        verbose_name_plural = 'imóveis'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f'{self.titulo}-{self.cidade}')[:170] or 'imovel'
            slug = base_slug
            suffix = 2
            while Imovel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug[:170]}-{suffix}'
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class Favorito(models.Model):
    """Imóvel que um usuário logado salvou como favorito (fica guardado no banco)."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoritos')
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='favoritado_por')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'imovel'], name='favorito_unico_por_usuario'),
        ]
        verbose_name = 'favorito'
        verbose_name_plural = 'favoritos'

    def __str__(self):
        return f'{self.usuario} ♥ {self.imovel}'


class FotoImovel(models.Model):
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='imoveis/%Y/%m/')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']
        verbose_name = 'foto do imóvel'
        verbose_name_plural = 'fotos dos imóveis'


class ConfiguracaoSite(models.Model):
    nome_site = models.CharField(max_length=120, default='UniLar')
    email_atendimento = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    informacoes_institucionais = models.TextField(blank=True)

    class Meta:
        verbose_name = 'configuração do site'
        verbose_name_plural = 'configurações do site'

    def __str__(self):
        return self.nome_site


@receiver(post_delete, sender=FotoImovel)
def remover_arquivo_foto(sender, instance, **kwargs):
    if instance.imagem:
        instance.imagem.delete(save=False)


@receiver(user_logged_in)
def juntar_favoritos_da_sessao(sender, request, user, **kwargs):
    """Ao entrar, os favoritos marcados antes do login passam a ficar salvos na conta."""
    sessao = getattr(request, 'session', None)
    slugs = sessao.pop('favoritos', []) if sessao is not None else []
    if slugs:
        Favorito.objects.bulk_create(
            [Favorito(usuario=user, imovel=imovel) for imovel in Imovel.objects.filter(slug__in=slugs)],
            ignore_conflicts=True,
        )
