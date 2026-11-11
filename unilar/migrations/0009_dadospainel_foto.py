from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unilar', '0008_favorito'),
    ]

    operations = [
        migrations.AddField(
            model_name='dadospainel',
            name='foto',
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='dadospainel',
            name='foto_atualizada_em',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
