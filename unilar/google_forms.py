from allauth.socialaccount.forms import SignupForm
from django import forms
from django.db import transaction

from .forms import UFS, CidadeUFMixin, validar_cpf
from .models import PerfilCadastro


class CadastroGoogleForm(CidadeUFMixin, SignupForm):
    nome = forms.CharField(max_length=150, label='Nome completo')
    cpf = forms.CharField(max_length=14, label='CPF')
    endereco = forms.CharField(max_length=200, label='Rua e número')
    uf = forms.ChoiceField(choices=UFS, label='Estado')
    cidade = forms.CharField(max_length=100, label='Cidade')
    aceite = forms.BooleanField(label='Li e concordo com os Termos de Uso e a Política de Privacidade.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True
        self.fields['nome'].initial = self.sociallogin.user.get_full_name()

    def clean_cpf(self):
        cpf = validar_cpf(self.cleaned_data['cpf'])
        if PerfilCadastro.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError('Este CPF já possui cadastro.')
        return cpf

    @transaction.atomic
    def save(self, request):
        user = super().save(request)
        dados = self.cleaned_data
        PerfilCadastro.objects.create(usuario=user, nome=dados['nome'], cpf=dados['cpf'],
                                      endereco=dados['endereco'], cidade=dados['cidade'])
        return user
