from datetime import datetime
import gzip
import json
import unicodedata
import urllib.request
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from django import forms
from django.core.cache import cache

from .models import COMODIDADES, ConfiguracaoSite, ContatoImovel, Imovel, SolicitacaoVisita


class ContatoImovelForm(forms.ModelForm):
    class Meta:
        model = ContatoImovel
        fields = ['nome', 'email', 'mensagem']


class DuvidaForm(forms.ModelForm):
    """Dúvida enviada pela página Dúvidas (somente usuários logados)."""
    assunto = forms.CharField(max_length=120, label='Assunto')
    mensagem = forms.CharField(max_length=3000, widget=forms.Textarea, label='Detalhes da dúvida')

    class Meta:
        model = ContatoImovel
        fields = ['assunto', 'mensagem']


class SolicitacaoVisitaForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoVisita
        fields = ['nome', 'email', 'data', 'horario', 'observacao']

    def clean(self):
        cleaned = super().clean()
        data = cleaned.get('data')
        horario = cleaned.get('horario')
        if horario and horario.strftime('%H:%M:%S') not in {
            '09:00:00', '10:00:00', '11:00:00', '14:00:00',
            '15:00:00', '16:00:00', '17:00:00',
        }:
            self.add_error('horario', 'Selecione um dos horários disponíveis.')
        if data and horario:
            fuso = ZoneInfo('America/Sao_Paulo')
            if datetime.combine(data, horario, tzinfo=fuso) <= datetime.now(fuso):
                self.add_error('data', 'Escolha uma data e um horário futuros.')
        return cleaned


def validar_cpf(cpf):
    import re
    if not re.fullmatch(r'[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', cpf):
        raise forms.ValidationError('Informe um CPF válido.')
    cpf = cpf.replace('.', '').replace('-', '')
    for tamanho in [9, 10]:
        soma = sum(int(n) * (tamanho + 1 - i) for i, n in enumerate(cpf[:tamanho]))
        digito = (soma * 10 % 11) % 10
        if len(set(cpf)) == 1 or int(cpf[tamanho]) != digito:
            raise forms.ValidationError('Informe um CPF válido.')
    return cpf


UFS = [
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
    ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
    ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
    ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
]
IBGE_MUNICIPIOS_URL = 'https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios'
# Lista oficial do IBGE salva no projeto (gerada com: python manage.py baixar_municipios).
MUNICIPIOS_ARQUIVO = Path(__file__).resolve().parent / 'front' / 'dados' / 'municipios.json'


def _normalizar(texto):
    sem_acento = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return ' '.join(sem_acento.casefold().split())


@lru_cache(maxsize=1)
def _municipios_do_arquivo():
    with open(MUNICIPIOS_ARQUIVO, encoding='utf-8') as arquivo:
        return json.load(arquivo)


def baixar_municipios_ibge(uf):
    requisicao = urllib.request.Request(
        IBGE_MUNICIPIOS_URL.format(uf=uf),
        headers={'User-Agent': 'UniLar/1.0', 'Accept-Encoding': 'gzip'},
    )
    with urllib.request.urlopen(requisicao, timeout=15) as resposta:
        conteudo = resposta.read()
    # A API do IBGE costuma responder compactada (gzip), mesmo sem pedir.
    if conteudo[:2] == b'\x1f\x8b':
        conteudo = gzip.decompress(conteudo)
    return [municipio['nome'] for municipio in json.loads(conteudo.decode('utf-8'))]


def municipios_da_uf(uf):
    """Municípios da UF: usa o arquivo salvo no projeto; sem ele, consulta a API do IBGE (cache de 24 h)."""
    if MUNICIPIOS_ARQUIVO.exists():
        return _municipios_do_arquivo().get(uf, [])
    chave = f'ibge-municipios-{uf}'
    nomes = cache.get(chave)
    if nomes is None:
        nomes = baixar_municipios_ibge(uf)
        cache.set(chave, nomes, 60 * 60 * 24)
    return nomes


def validar_cidade(uf, cidade):
    """Confere a cidade na lista do IBGE e devolve no padrão do banco: 'Patos de Minas - MG'."""
    try:
        nomes = municipios_da_uf(uf)
    except (OSError, ValueError, KeyError):
        raise forms.ValidationError('Não foi possível validar a cidade agora. Tente novamente em instantes.')
    alvo = _normalizar(cidade)
    for nome in nomes:
        if _normalizar(nome) == alvo:
            return f'{nome} - {uf}'
    raise forms.ValidationError('Selecione uma cidade da lista.')


class CidadeUFMixin:
    """Valida o par estado/cidade e grava a cidade no formato padronizado."""

    def clean(self):
        dados = super().clean()
        uf, cidade = dados.get('uf'), dados.get('cidade')
        if uf and cidade:
            try:
                dados['cidade'] = validar_cidade(uf, cidade)
            except forms.ValidationError as erro:
                self.add_error('cidade', erro)
        return dados


class CadastroForm(CidadeUFMixin, forms.Form):
    nome = forms.CharField(max_length=150, label='Nome completo')
    cpf = forms.CharField(max_length=14, label='CPF')
    email = forms.EmailField(max_length=150, label='E-mail')
    senha = forms.CharField(strip=False, widget=forms.PasswordInput, label='Senha')
    confirmar = forms.CharField(strip=False, widget=forms.PasswordInput, label='Confirmar senha')
    aceite = forms.BooleanField()
    endereco = forms.CharField(max_length=200, label='Rua e número')
    uf = forms.ChoiceField(choices=UFS, label='Estado')
    cidade = forms.CharField(max_length=100, label='Cidade')

    def clean_cpf(self):
        return validar_cpf(self.cleaned_data['cpf'])

    def clean(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        dados = super().clean()
        email = dados.get('email', '').lower()
        dados['email'] = email
        if dados.get('senha'):
            try:
                validate_password(dados['senha'], get_user_model()(username=email, email=email))
            except ValidationError as erro:
                self.add_error('senha', erro)
        if dados.get('confirmar') and dados.get('confirmar') != self.data.get('senha'):
            self.add_error('confirmar', 'As senhas precisam ser iguais.')
        return dados


class PerfilPainelForm(forms.ModelForm):
    nome = forms.CharField(max_length=150, label='Nome completo')

    class Meta:
        from .models import DadosPainel
        model = DadosPainel
        fields = ['nome', 'telefone', 'curso', 'universidade']


FOTO_PERFIL_TAMANHO_MAXIMO = 4 * 1024 * 1024  # 4 MB (a Vercel recusa envios acima de 4,5 MB)
FOTO_PERFIL_LADO = 320


class FotoPerfilForm(forms.Form):
    foto = forms.ImageField(label='Foto de perfil')

    def clean_foto(self):
        from io import BytesIO
        from PIL import Image, ImageOps

        arquivo = self.cleaned_data['foto']
        if arquivo.size > FOTO_PERFIL_TAMANHO_MAXIMO:
            raise forms.ValidationError('A imagem deve ter no máximo 4 MB.')
        try:
            arquivo.seek(0)
            imagem = Image.open(arquivo)
            if imagem.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise forms.ValidationError('Envie uma imagem JPG, PNG ou WEBP.')
            if imagem.width * imagem.height > 40_000_000:
                raise forms.ValidationError('A imagem é grande demais. Use uma foto menor.')
            imagem = ImageOps.exif_transpose(imagem).convert('RGB')
        except forms.ValidationError:
            raise
        except Exception:
            raise forms.ValidationError('Não foi possível ler a imagem. Envie outro arquivo.')
        # Recorta no centro em formato quadrado, reduz e regrava como JPEG.
        # Regravar descarta metadados (como localização GPS) e qualquer conteúdo escondido no arquivo.
        imagem = ImageOps.fit(imagem, (FOTO_PERFIL_LADO, FOTO_PERFIL_LADO), Image.Resampling.LANCZOS)
        saida = BytesIO()
        imagem.save(saida, format='JPEG', quality=85, optimize=True)
        return saida.getvalue()


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super().clean(upload, initial) for upload in files]


class AdminImovelForm(forms.ModelForm):
    comodidades = forms.MultipleChoiceField(
        choices=[(chave, nome) for chave, nome, _ in COMODIDADES],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Comodidades e contas inclusas',
        help_text='Marque tudo o que o imóvel oferece. A página do anúncio monta os destaques a partir disso.',
    )
    fotos = MultipleImageField(
        required=False,
        label='Adicionar fotos',
        help_text='Selecione uma ou mais imagens. As fotos atuais são mantidas.',
    )

    class Meta:
        model = Imovel
        fields = [
            'titulo', 'descricao', 'preco', 'endereco', 'bairro', 'cidade', 'proximidades',
            'tipo', 'capacidade', 'quartos', 'camas', 'banheiros', 'vagas', 'area',
            'comodidades', 'informacoes_adicionais', 'status', 'proprietario',
        ]
        labels = {
            'capacidade': 'Quantas pessoas',
            'proximidades': 'O que tem por perto',
            'informacoes_adicionais': 'Regras e informações adicionais',
        }
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'informacoes_adicionais': forms.Textarea(attrs={'rows': 3}),
            'preco': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'quartos': forms.NumberInput(attrs={'min': '0'}),
            'banheiros': forms.NumberInput(attrs={'min': '0'}),
            'vagas': forms.NumberInput(attrs={'min': '0'}),
            'area': forms.NumberInput(attrs={'min': '1'}),
            'capacidade': forms.NumberInput(attrs={'min': '1'}),
            'camas': forms.NumberInput(attrs={'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('capacidade', 'camas'):
            self.fields[campo].required = False

    def clean_capacidade(self):
        return self.cleaned_data.get('capacidade') or 1

    def clean_camas(self):
        valor = self.cleaned_data.get('camas')
        return 1 if valor is None else valor

    def clean_fotos(self):
        fotos = self.cleaned_data['fotos']
        for foto in fotos:
            if foto.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Cada imagem deve ter no máximo 10 MB.')
        return fotos


class AdminConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSite
        fields = [
            'nome_site', 'email_atendimento', 'telefone', 'instagram',
            'facebook', 'informacoes_institucionais',
        ]
        widgets = {'informacoes_institucionais': forms.Textarea(attrs={'rows': 5})}
