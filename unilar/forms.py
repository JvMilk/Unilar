from datetime import datetime
from zoneinfo import ZoneInfo

from django import forms

from .models import ContatoImovel, SolicitacaoVisita


class ContatoImovelForm(forms.ModelForm):
    class Meta:
        model = ContatoImovel
        fields = ['nome', 'email', 'mensagem']


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


class CadastroForm(forms.Form):
    nome = forms.CharField(max_length=150, label='Nome completo')
    cpf = forms.CharField(max_length=14, label='CPF')
    email = forms.EmailField(max_length=150, label='E-mail')
    senha = forms.CharField(strip=False, widget=forms.PasswordInput, label='Senha')
    confirmar = forms.CharField(strip=False, widget=forms.PasswordInput, label='Confirmar senha')
    aceite = forms.BooleanField()
    endereco = forms.CharField(max_length=200, label='Rua e número')
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
