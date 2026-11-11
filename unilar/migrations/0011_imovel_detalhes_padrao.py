from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unilar', '0010_contatoimovel_assunto_usuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='imovel',
            name='capacidade',
            field=models.PositiveSmallIntegerField(default=1, help_text='Quantas pessoas podem morar no imóvel'),
        ),
        migrations.AddField(
            model_name='imovel',
            name='camas',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='imovel',
            name='comodidades',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='imovel',
            name='proximidades',
            field=models.CharField(blank=True, help_text='O que tem por perto. Ex.: em frente ao shopping, a 5 minutos da UNIPAM', max_length=160),
        ),
    ]
