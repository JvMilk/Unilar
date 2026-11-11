import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unilar', '0007_alter_imovel_options_alter_imovel_area_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('imovel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favoritado_por', to='unilar.imovel')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favoritos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'favorito',
                'verbose_name_plural': 'favoritos',
                'ordering': ['-criado_em'],
                'constraints': [models.UniqueConstraint(fields=('usuario', 'imovel'), name='favorito_unico_por_usuario')],
            },
        ),
    ]
