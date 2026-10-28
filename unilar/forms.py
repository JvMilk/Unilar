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
