import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unilar', '0009_dadospainel_foto'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='contatoimovel',
            name='assunto',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='contatoimovel',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='duvidas', to=settings.AUTH_USER_MODEL),
        ),
    ]
