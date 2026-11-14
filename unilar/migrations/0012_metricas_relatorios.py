import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('unilar', '0011_imovel_detalhes_padrao'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcessoDiario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia', models.DateField(unique=True)),
                ('visualizacoes', models.PositiveBigIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='AluguelConfirmado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registrado_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('imovel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='unilar.imovel')),
            ],
        ),
    ]
