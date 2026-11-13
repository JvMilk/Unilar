from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand, CommandError

from unilar.models import FotoImovel


class Command(BaseCommand):
    help = 'Envia para o Supabase Storage as fotos de imóveis que estão na pasta media/ deste computador.'

    def handle(self, *args, **options):
        if settings.STORAGES['default']['BACKEND'].endswith('FileSystemStorage'):
            raise CommandError(
                'O Supabase Storage não está configurado. Defina SUPABASE_S3_ACCESS_KEY_ID e '
                'SUPABASE_S3_SECRET_ACCESS_KEY neste terminal e rode de novo.'
            )
        local = FileSystemStorage(location=settings.MEDIA_ROOT)
        enviadas = ja_existiam = faltando = 0
        for foto in FotoImovel.objects.select_related('imovel'):
            nome = foto.imagem.name
            if default_storage.exists(nome):
                ja_existiam += 1
                continue
            if not local.exists(nome):
                faltando += 1
                self.stdout.write(self.style.WARNING(f'Não encontrada neste computador: {nome} ({foto.imovel})'))
                continue
            with local.open(nome, 'rb') as arquivo:
                salvo = default_storage.save(nome, arquivo)
            if salvo != nome:
                foto.imagem.name = salvo
                foto.save(update_fields=['imagem'])
            enviadas += 1
            self.stdout.write(f'Enviada: {nome}')
        self.stdout.write(self.style.SUCCESS(
            f'Pronto: {enviadas} enviada(s), {ja_existiam} já estavam no Supabase, {faltando} não encontrada(s).'
        ))
