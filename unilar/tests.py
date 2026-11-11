from datetime import datetime, timedelta
from io import BytesIO
import os
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import ContatoImovel, Imovel, PerfilCadastro, SolicitacaoVisita


class IntegracaoImovelTests(TestCase):
    def test_paginas_e_navegacao(self):
        for name in ['login', 'detalhe_imovel', 'favoritos']:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse('imoveis')).status_code, 200)

    def test_catalogo_filtra_e_preserva_imoveis_distintos(self):
        response = self.client.get(reverse('imoveis'), {'tipo': 'kitnet'})
        self.assertEqual({i['slug'] for i in response.context['imoveis']},
                         {'kitnet-centro-patos', 'kitnet-no-centro', 'kitnet-moderna'})
        response = self.client.get(reverse('imoveis'), {'cidade': 'Rio Paranaíba - MG', 'preco': 'ate-800'})
        self.assertEqual([i['slug'] for i in response.context['imoveis']], ['kitnet-no-centro'])
        self.assertEqual(self.client.get(reverse('imoveis'), {'cidade': 'inexistente'}).context['imoveis'], [])

    def test_favoritos_catalogo_compartilham_sessao_com_detalhes(self):
        url = reverse('favoritar_catalogo', args=['kitnet-no-centro'])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertTrue(self.client.get(reverse('detalhe_imovel')).context['favorito'])
        self.client.post(reverse('favoritar_imovel'))
        self.assertEqual(self.client.get(reverse('favoritos')).context['imoveis'], [])
        self.assertEqual(self.client.post(reverse('favoritar_catalogo', args=['inexistente'])).status_code, 404)

    def test_contato_salvo_com_validacao(self):
        url = reverse('contato_imovel')
        response = self.client.post(url, {'nome': 'Teste', 'email': 'invalido', 'mensagem': 'Olá'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ContatoImovel.objects.exists())
        response = self.client.post(url, {'nome': 'Teste', 'email': 'teste@example.com', 'mensagem': 'Tenho interesse.'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContatoImovel.objects.get().mensagem, 'Tenho interesse.')

    def test_visita_rejeita_passado_e_horario_invalido(self):
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        data = {'nome': 'Teste', 'email': 'teste@example.com', 'horario': '09:00'}
        data['data'] = (hoje - timedelta(days=1)).isoformat()
        self.assertEqual(self.client.post(reverse('solicitar_visita'), data).status_code, 400)
        data.update(data=(hoje + timedelta(days=2)).isoformat(), horario='03:00')
        self.assertEqual(self.client.post(reverse('solicitar_visita'), data).status_code, 400)
        self.assertFalse(SolicitacaoVisita.objects.exists())
        data['horario'] = '14:00'
        self.assertEqual(self.client.post(reverse('solicitar_visita'), data).status_code, 201)
        self.assertEqual(SolicitacaoVisita.objects.get().nome, 'Teste')

    def test_favoritos_persistem_na_sessao_e_sao_isolados(self):
        url = reverse('favoritar_imovel')
        self.assertTrue(self.client.post(url).json()['favorito'])
        self.assertTrue(self.client.get(reverse('detalhe_imovel')).context['favorito'])
        self.assertTrue(self.client.get(reverse('favoritos')).context['favorito'])
        self.assertFalse(Client().get(reverse('favoritos')).context['favorito'])
        self.assertFalse(self.client.post(url).json()['favorito'])

    def test_endpoints_exigem_post_e_csrf(self):
        protected = Client(enforce_csrf_checks=True)
        for name in ['contato_imovel', 'solicitar_visita', 'favoritar_imovel']:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 405)
                self.assertEqual(protected.post(reverse(name)).status_code, 403)
        protected.get(reverse('detalhe_imovel'))
        token = protected.cookies['csrftoken'].value
        self.assertEqual(protected.post(reverse('favoritar_imovel'), HTTP_X_CSRFTOKEN=token).status_code, 200)

@patch('unilar.forms.municipios_da_uf', return_value=['Patos de Minas', 'Rio Paranaíba'])
class CadastroTests(TestCase):
    def test_cadastro_login_e_duplicidade(self, _municipios):
        from django.contrib.auth import get_user_model
        from .models import PerfilCadastro
        dados = dict(nome='Pessoa de Teste', cpf='529.982.247-25', email='teste@example.org',
                     senha='Teste!98765abc', confirmar='Teste!98765abc', aceite='on',
                     endereco='Rua de teste, 10', uf='MG', cidade='Patos de Minas')
        url = reverse('cadastro')
        self.assertContains(self.client.get(url), 'Crie sua conta')
        self.assertFalse(self.client.post(url, {**dados, 'cpf':'11111111111'}).context['form'].is_valid())
        self.assertRedirects(self.client.post(url, dados), reverse('login'))
        self.assertTrue(get_user_model().objects.get().check_password(dados['senha']))
        self.assertEqual(PerfilCadastro.objects.get().cpf, '52998224725')
        self.assertEqual(PerfilCadastro.objects.get().cidade, 'Patos de Minas - MG')
        self.client.post(url, {**dados, 'email':'outra@example.org'})
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertRedirects(self.client.post(reverse('login'), dados), reverse('inicio'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_bloqueado_apos_tentativas(self, _municipios):
        from django.contrib.auth import get_user_model
        get_user_model().objects.create_user(username='aluno@teste.com', email='aluno@teste.com', password='SenhaForte@2026')
        for _ in range(5):
            self.client.post(reverse('login'), {'email': 'aluno@teste.com', 'senha': 'errada'})
        resposta = self.client.post(reverse('login'), {'email': 'aluno@teste.com', 'senha': 'SenhaForte@2026'})
        self.assertEqual(resposta.status_code, 429)
        self.assertContains(resposta, 'Muitas tentativas', status_code=429)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cidade_padronizada_e_fora_da_lista(self, _municipios):
        from .forms import validar_cidade
        from django import forms as dj_forms
        self.assertEqual(validar_cidade('MG', '  rio paranaiba '), 'Rio Paranaíba - MG')
        with self.assertRaises(dj_forms.ValidationError):
            validar_cidade('MG', 'Cidade inventada')


class PainelTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.usuario = get_user_model().objects.create_user(
            username='painel@example.com', email='painel@example.com', password='Teste123!')

    def test_exige_login(self):
        self.assertEqual(self.client.get('/painel/').status_code, 302)

    def test_perfil_legado_e_edicao(self):
        from .models import DadosPainel
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get('/painel/'), 'Meu perfil')
        response = self.client.post('/painel/', {
            'nome': 'Nome atualizado', 'telefone': '(34) 99999-1234',
            'curso': 'Sistemas de Informação', 'universidade': 'Unipam'})
        self.assertRedirects(response, '/painel/')
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, 'Nome atualizado')
        self.assertEqual(DadosPainel.objects.get(usuario=self.usuario).curso,
                         'Sistemas de Informação')

    def test_favoritos_visitas_e_saida(self):
        self.client.force_login(self.usuario)
        self.client.post('/catalogo/kitnet-no-centro/favoritar/')
        self.client.get('/imoveis/kitnet-no-centro/')
        response = self.client.get('/painel/')
        self.assertEqual([i['slug'] for i in response.context['salvos']], ['kitnet-no-centro'])
        self.assertEqual([i['slug'] for i in response.context['visitados']], ['kitnet-no-centro'])
        self.assertEqual(self.client.get('/sair/').status_code, 405)
        self.client.post('/sair/')
        self.assertEqual(self.client.get('/painel/').status_code, 302)


class AdminAreaTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.user = get_user_model().objects.create_user(
            username='anunciante@example.com',
            email='anunciante@example.com',
            password='Teste123!',
        )
        self.staff = get_user_model().objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='Teste123!',
            is_staff=True,
        )
        self.client.force_login(self.staff)

    def dados_imovel(self, **overrides):
        dados = {
            'titulo': 'Residência de teste',
            'descricao': 'Imóvel amplo perto da universidade.',
            'preco': '980.50',
            'endereco': 'Rua das Flores, 10',
            'bairro': 'Centro',
            'cidade': 'Patos de Minas - MG',
            'quartos': '2',
            'banheiros': '1',
            'vagas': '1',
            'area': '55',
            'tipo': 'apartamento',
            'informacoes_adicionais': 'Aceita estudantes.',
            'status': 'disponivel',
            'proprietario': str(self.user.pk),
        }
        dados.update(overrides)
        return dados

    def test_painel_e_secoes_exigem_usuario_staff(self):
        self.client.logout()
        urls = [
            reverse('admin_dashboard'),
            reverse('admin_relatorios'),
            reverse('admin_imoveis'),
            reverse('admin_anuncios'),
            reverse('admin_mensagens'),
            reverse('admin_usuarios'),
            reverse('admin_configuracoes'),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('admin_dashboard')).status_code, 302)
        self.client.force_login(self.staff)
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_dashboard_usa_metricas_reais_e_filtro_de_periodo(self):
        imovel = Imovel.objects.get(slug='kitnet-no-centro')
        contato = ContatoImovel.objects.create(
            imovel=imovel.slug,
            nome='Visitante do painel',
            email='visitante@example.com',
            mensagem='Gostaria de agendar uma visita.',
        )
        response = self.client.get(reverse('admin_dashboard'), {'periodo': '7'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<body class="admin-page">', html=False)
        self.assertContains(response, 'css/admin.css?v=20261105-2')
        self.assertEqual(response.context['total_imoveis'], Imovel.objects.count())
        self.assertEqual(response.context['disponiveis'], Imovel.objects.filter(status=Imovel.Status.DISPONIVEL).count())
        self.assertEqual(response.context['alugados'], Imovel.objects.filter(status=Imovel.Status.ALUGADO).count())
        self.assertEqual(response.context['duvidas_pendentes'], 1)
        self.assertEqual(len(response.context['chart_labels']), 7)
        self.assertEqual(sum(response.context['chart_questions']), 1)
        self.assertContains(response, 'Atividade dos anúncios')
        self.assertContains(response, 'Últimas dúvidas')
        self.assertContains(response, reverse('admin_mensagens_detalhe', args=[contato.pk]))
        self.assertContains(response, 'VD')
        self.assertContains(response, 'Opções para')
        for item in [
            'Imóveis cadastrados', 'Disponíveis', 'Alugados',
            'Dúvidas pendentes', 'Imóveis recentes',
        ]:
            with self.subTest(item=item):
                self.assertContains(response, item)
        self.assertContains(response, 'csrfmiddlewaretoken')
        for recente in response.context['recentes']:
            self.assertContains(response, reverse('admin_imovel_editar', args=[recente.pk]))
            self.assertContains(response, reverse('admin_imovel_excluir', args=[recente.pk]))
        response = self.client.get(reverse('admin_dashboard'), {'periodo': '90'})
        self.assertEqual(len(response.context['chart_labels']), 90)

        report = self.client.get(reverse('admin_relatorios'))
        self.assertEqual(report.status_code, 200)
        self.assertEqual(len(report.context['relatorio']), 12)
        self.assertContains(report, 'Atividade mensal')

    def test_login_admin_abre_dashboard_e_mostra_acesso_no_site(self):
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'email': self.staff.email,
            'senha': 'Teste123!',
        })
        self.assertRedirects(response, reverse('admin_dashboard'))
        self.assertContains(self.client.get(reverse('inicio')), 'Administração')

    def test_csrf_aceita_localhost_https_e_origin_codespaces_sem_desativar_protecao(self):
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)
        self.assertIn('https://localhost:8001', settings.CSRF_TRUSTED_ORIGINS)
        self.assertTrue(any(origin.startswith('https://*.') for origin in settings.CSRF_TRUSTED_ORIGINS))

        codespace = os.environ.get('CODESPACE_NAME', 'test-codespace')
        domain = os.environ.get(
            'GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'app.github.dev',
        ).lstrip('.')
        host = f'{codespace}-8001.{domain}'
        self.assertTrue(
            any(host == allowed or allowed.startswith('.') and host.endswith(allowed)
                for allowed in settings.ALLOWED_HOSTS)
        )

        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.get(reverse('login'), HTTP_HOST=host).status_code, 200)
        csrf_token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('login'),
            {'email': self.staff.email, 'senha': 'Teste123!'},
            HTTP_HOST=host,
            HTTP_ORIGIN='https://localhost:8001',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 302)

        denied = Client(enforce_csrf_checks=True)
        denied.force_login(self.staff)
        response = denied.post(
            reverse('admin_imovel_novo'),
            self.dados_imovel(),
            HTTP_HOST=host,
            HTTP_ORIGIN='https://attacker.example',
        )
        self.assertEqual(response.status_code, 403)

        page = client.get(reverse('admin_imovel_novo'), HTTP_HOST=host)
        self.assertEqual(page.status_code, 200)
        csrf_token = client.cookies['csrftoken'].value
        origin = f'https://{host}'
        response = client.post(
            reverse('admin_imovel_novo'),
            self.dados_imovel(),
            HTTP_HOST=host,
            HTTP_ORIGIN=origin,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 302)
        imovel = Imovel.objects.get(titulo='Residência de teste')

        page = client.get(reverse('admin_imovel_editar', args=[imovel.pk]), HTTP_HOST=host)
        self.assertEqual(page.status_code, 200)
        csrf_token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('admin_imovel_editar', args=[imovel.pk]),
            self.dados_imovel(titulo='Imóvel editado com CSRF'),
            HTTP_HOST=host,
            HTTP_ORIGIN=origin,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 302)
        imovel.refresh_from_db()
        self.assertEqual(imovel.titulo, 'Imóvel editado com CSRF')

        page = client.get(reverse('admin_imoveis'), HTTP_HOST=host)
        self.assertEqual(page.status_code, 200)
        csrf_token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('admin_imovel_excluir', args=[imovel.pk]),
            HTTP_HOST=host,
            HTTP_ORIGIN=origin,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Imovel.objects.filter(pk=imovel.pk).exists())

    def test_cria_edita_fotos_publica_e_exclui_imovel(self):
        from PIL import Image

        buffer = BytesIO()
        Image.new('RGB', (12, 12), color='blue').save(buffer, format='PNG')
        imagem = SimpleUploadedFile('capa.png', buffer.getvalue(), content_type='image/png')
        with tempfile.TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            response = self.client.post(
                reverse('admin_imovel_novo'),
                {
                    **self.dados_imovel(cidade='Uberaba - MG', tipo=Imovel.Tipo.OUTRO),
                    'fotos': [imagem],
                },
            )
            self.assertRedirects(response, reverse('admin_imoveis'))
            imovel = Imovel.objects.get(titulo='Residência de teste')
            self.assertEqual(imovel.proprietario, self.user)
            self.assertEqual(imovel.fotos.count(), 1)
            arquivo_foto = imovel.fotos.first().imagem.path
            destaques = self.client.get(reverse('inicio')).context['imoveis']
            self.assertIn(imovel.slug, {item['slug'] for item in destaques})
            self.assertContains(
                self.client.get(reverse('imoveis'), {
                    'cidade': 'Uberaba - MG', 'tipo': Imovel.Tipo.OUTRO,
                }),
                'Residência de teste',
            )
            self.assertContains(
                self.client.get(reverse('admin_imoveis'), {'q': 'Rua das Flores, 10'}),
                'Residência de teste',
            )
            self.assertContains(self.client.get(reverse('imoveis')), 'Residência de teste')
            self.assertContains(self.client.get(reverse('imovel_publico', args=[imovel.slug])), 'Aceita estudantes.')

            response = self.client.post(
                reverse('admin_imovel_editar', args=[imovel.pk]),
                self.dados_imovel(titulo='Residência atualizada', status='alugado'),
            )
            self.assertRedirects(response, reverse('admin_imoveis'))
            imovel.refresh_from_db()
            self.assertEqual(imovel.titulo, 'Residência atualizada')
            self.assertEqual(imovel.status, Imovel.Status.ALUGADO)
            self.assertNotContains(self.client.get(reverse('imoveis')), 'Residência atualizada')
            self.assertEqual(self.client.get(reverse('imovel_publico', args=[imovel.slug])).status_code, 404)

            response = self.client.post(reverse('admin_imovel_excluir', args=[imovel.pk]))
            self.assertRedirects(response, reverse('admin_imoveis'))
            self.assertFalse(Imovel.objects.filter(pk=imovel.pk).exists())
            self.assertFalse(Path(arquivo_foto).exists())

    def test_edicoes_do_catalogo_refletem_no_detalhe_publico_legado(self):
        imovel = Imovel.objects.get(slug='kitnet-no-centro')
        response = self.client.post(
            reverse('admin_imovel_editar', args=[imovel.pk]),
            self.dados_imovel(titulo='Kitnet atualizada', preco='1050.00'),
        )
        self.assertRedirects(response, reverse('admin_imoveis'))
        self.assertContains(self.client.get(reverse('detalhe_imovel')), 'Kitnet atualizada')
        self.assertContains(self.client.get(reverse('imoveis'), {'q': 'Kitnet atualizada'}), 'Kitnet atualizada')

        self.client.post(
            reverse('admin_anuncio_status', args=[imovel.pk]),
            {'status': Imovel.Status.ALUGADO},
        )
        self.assertEqual(self.client.get(reverse('detalhe_imovel')).status_code, 404)
        self.assertNotContains(self.client.get(reverse('imoveis')), 'Kitnet atualizada')

    def test_moderacao_mensagens_e_resposta_publica(self):
        imovel = Imovel.objects.create(
            proprietario=self.user,
            titulo='Casa para consulta',
            descricao='Casa para locação.',
            preco='900.00',
            endereco='Rua das Acácias, 3',
            bairro='Jardim',
            cidade='Patos de Minas - MG',
            quartos=2,
            banheiros=1,
            vagas=1,
            area=60,
            tipo=Imovel.Tipo.CASA,
        )
        response = self.client.post(reverse('contato_imovel_publico', args=[imovel.slug]), {
            'nome': 'Visitante', 'email': 'visitante@example.com', 'mensagem': 'O imóvel aceita pets?',
        })
        self.assertRedirects(response, reverse('imovel_publico', args=[imovel.slug]))
        duvida = ContatoImovel.objects.get(email='visitante@example.com')
        response = self.client.post(reverse('admin_mensagem_responder', args=[duvida.pk]), {
            'acao': 'responder', 'resposta': 'Sim, consulte as condições com a equipe.',
        })
        self.assertRedirects(response, reverse('admin_mensagens_detalhe', args=[duvida.pk]))
        duvida.refresh_from_db()
        self.assertEqual(duvida.status, ContatoImovel.Status.RESPONDIDA)
        self.assertTrue(duvida.respondido_em)
        self.assertContains(self.client.get(reverse('admin_mensagens_detalhe', args=[duvida.pk])), duvida.resposta)
        self.client.post(reverse('admin_mensagem_responder', args=[duvida.pk]), {'acao': 'pendente'})
        duvida.refresh_from_db()
        self.assertEqual(duvida.status, ContatoImovel.Status.PENDENTE)
        self.client.post(reverse('admin_mensagem_responder', args=[duvida.pk]), {'acao': 'excluir'})
        self.assertFalse(ContatoImovel.objects.filter(pk=duvida.pk).exists())

    def test_anuncios_usuarios_e_configuracoes(self):
        imovel = Imovel.objects.get(slug='kitnet-no-centro')
        self.client.post(reverse('admin_anuncio_status', args=[imovel.pk]), {'status': 'pendente'})
        imovel.refresh_from_db()
        self.assertEqual(imovel.status, Imovel.Status.PENDENTE)

        PerfilCadastro.objects.create(
            usuario=self.user, nome='Anunciante de Teste', cpf='52998224725',
            endereco='Rua das Flores, 10', cidade='Patos de Minas',
        )
        self.assertContains(
            self.client.get(reverse('admin_usuarios'), {'usuario': self.user.pk}),
            '52998224725',
        )
        self.assertContains(
            self.client.get(reverse('admin_usuarios'), {'q': 'Anunciante de Teste'}),
            'Anunciante de Teste',
        )
        self.client.post(reverse('admin_usuario_atualizar', args=[self.user.pk]), {'acao': 'ativo'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(
            self.client.post(
                reverse('admin_usuario_atualizar', args=[self.user.pk]),
                {'acao': 'staff'},
            ).status_code,
            403,
        )

        response = self.client.post(reverse('admin_configuracoes'), {
            'nome_site': 'UniLar Institucional',
            'email_atendimento': 'atendimento@example.com',
            'telefone': '(34) 3000-0000',
            'instagram': 'https://instagram.com/unilar',
            'facebook': 'https://facebook.com/unilar',
            'informacoes_institucionais': 'Moradia para estudantes.',
        })
        self.assertRedirects(response, reverse('admin_configuracoes'))
        self.assertContains(self.client.get(reverse('inicio')), '<title>Imóveis em destaque | UniLar Institucional</title>', html=False)

    def test_admin_superusuario_pode_conceder_acesso_administrativo(self):
        from django.contrib.auth import get_user_model
        superuser = get_user_model().objects.create_superuser(
            username='root@example.com',
            email='root@example.com',
            password='Teste123!',
        )
        self.client.force_login(superuser)
        self.client.post(reverse('admin_usuario_atualizar', args=[self.user.pk]), {'acao': 'staff'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)
