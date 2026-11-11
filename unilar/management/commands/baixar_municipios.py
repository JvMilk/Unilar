import json

from django.core.management.base import BaseCommand

from unilar.forms import MUNICIPIOS_ARQUIVO, UFS, _normalizar, baixar_municipios_ibge


class Command(BaseCommand):
    help = 'Baixa a lista oficial de municípios do IBGE e salva em unilar/front/dados/municipios.json'

    def handle(self, *args, **options):
        dados = {}
        for sigla, nome in UFS:
            dados[sigla] = sorted(baixar_municipios_ibge(sigla), key=_normalizar)
            self.stdout.write(f'{sigla} ({nome}): {len(dados[sigla])} municípios')
        MUNICIPIOS_ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
        with open(MUNICIPIOS_ARQUIVO, 'w', encoding='utf-8') as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, separators=(',', ':'))
        total = sum(len(nomes) for nomes in dados.values())
        self.stdout.write(self.style.SUCCESS(f'Lista salva com {total} municípios em {MUNICIPIOS_ARQUIVO}'))
