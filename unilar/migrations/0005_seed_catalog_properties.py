from django.db import migrations


PROPERTIES = [
    ('apartamento-centro-patos', 'Apartamento no Centro', 'apartamento', 'Patos de Minas - MG', 'Centro', 1200, 2, 1, 0, 45, 'imagens/imovel-1.jpg', 'Apartamento para aluguel no Centro.', ''),
    ('kitnet-centro-patos', 'Kitnet no Centro', 'kitnet', 'Patos de Minas - MG', 'Centro', 750, 1, 1, 0, 20, 'imagens/imovel-2.jpg', 'Kitnet para aluguel no Centro.', ''),
    ('casa-compartilhada', 'Casa compartilhada', 'casa-compartilhada', 'Rio Paranaíba - MG', '', 900, 3, 2, 0, 120, 'imagens/imovel-3.jpg', 'Casa compartilhada para aluguel.', ''),
    ('apartamento-mobiliado', 'Apartamento mobiliado', 'apartamento', 'Patos de Minas - MG', '', 1400, 2, 1, 0, 60, 'imagens/imovel-4.jpg', 'Apartamento mobiliado para aluguel.', ''),
    ('kitnet-no-centro', 'Kitnet no Centro', 'kitnet', 'Rio Paranaíba - MG', 'Centro', 750, 1, 1, 0, 20, 'imagens/apartamento-1.jpg', 'Kitnet mobiliada, ideal para estudantes.', ''),
    ('apartamento-aconchegante', 'Apartamento aconchegante', 'apartamento', 'Patos de Minas - MG', 'Centro', 1450, 2, 1, 0, 68, 'imagens/listagem-1.jpg', 'Apartamento bem iluminado, com ambientes funcionais e acesso fácil a comércios e serviços.', 'Destaque'),
    ('casa-com-quintal', 'Casa com quintal', 'casa', 'Patos de Minas - MG', 'Jardim', 2200, 3, 2, 0, 120, 'imagens/listagem-2.jpg', 'Casa espaçosa com quintal, ideal para quem busca mais espaço e tranquilidade.', 'Ótima opção'),
    ('kitnet-moderna', 'Kitnet moderna', 'kitnet', 'Patos de Minas - MG', 'Centro', 1100, 1, 1, 0, 38, 'imagens/listagem-3.jpg', 'Kitnet compacta e moderna, uma opção prática para morar perto da região central.', 'Compacto'),
    ('apartamento-familiar', 'Apartamento familiar', 'apartamento', 'Patos de Minas - MG', 'Planalto', 1850, 3, 2, 0, 92, 'imagens/listagem-4.jpg', 'Apartamento confortável com três quartos e espaço para toda a família.', 'Novo'),
    ('casa-perto-de-tudo', 'Casa perto de tudo', 'casa', 'Patos de Minas - MG', 'Centro', 2700, 3, 2, 0, 135, 'imagens/listagem-5.jpg', 'Casa com boa distribuição dos cômodos e localização conveniente para o dia a dia.', 'Espaçosa'),
    ('apartamento-com-varanda', 'Apartamento com varanda', 'apartamento', 'Patos de Minas - MG', 'Jardim', 1650, 2, 2, 0, 75, 'imagens/listagem-6.jpg', 'Apartamento com varanda e ambientes agradáveis para relaxar depois de um dia cheio.', 'Varanda'),
]


def popular_catalogo(apps, schema_editor):
    Imovel = apps.get_model('unilar', 'Imovel')
    Imovel.objects.bulk_create([
        Imovel(
            slug=slug,
            titulo=titulo,
            tipo=tipo,
            cidade=cidade,
            bairro=bairro,
            preco=preco,
            quartos=quartos,
            banheiros=banheiros,
            vagas=vagas,
            area=area,
            endereco=bairro or cidade,
            descricao=descricao,
            imagem_padrao=imagem,
            destaque=destaque,
            status='disponivel',
        )
        for slug, titulo, tipo, cidade, bairro, preco, quartos, banheiros, vagas,
        area, imagem, descricao, destaque in PROPERTIES
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('unilar', '0004_configuracaosite_contatoimovel_respondido_em_and_more'),
    ]

    operations = [
        migrations.RunPython(popular_catalogo, migrations.RunPython.noop),
    ]
