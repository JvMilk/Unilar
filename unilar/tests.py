from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import Client, TestCase
from django.urls import reverse

from .models import ContatoImovel, SolicitacaoVisita


class IntegracaoImovelTests(TestCase):
    def test_paginas_e_navegacao(self):
        for name in ['login', 'detalhe_imovel', 'favoritos']:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse('imoveis')).status_code, 200)

    def test_catalogo_filtra_e_preserva_imoveis_distintos(self):
        response = self.client.get(reverse('imoveis'), {'tipo': 'kitnet'})
        self.assertEqual(len(response.context['imoveis']), 2)
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
