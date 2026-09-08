from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class DashboardProtecaoLoginTests(TestCase):
    """
    Teste de regressão do erro 500 em fotoid.photum.com.br.

    As views de dashboard foram extraídas do antigo views.py monolítico sem os
    decorators de autenticação. Com um usuário anônimo (AnonymousUser), a view
    /dashboard/ chamava request.user.guias_dashboard_permitidas() — método que
    só existe no modelo Usuario — e quebrava com AttributeError -> HTTP 500.

    Correção: @login_required + @never_cache restaurados. Anônimos devem ser
    redirecionados para /login/ (e nunca receber 500 ou dados sem autenticação).
    """

    # --- Views que quebravam com AnonymousUser (AttributeError) -------------

    def test_dashboard_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_dashboard_inteligente_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('dashboard_inteligente'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_dashboard_coordenador_fotografo_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('dashboard_coordenador_fotografo'))
        self.assertEqual(resp.status_code, 302)

    def test_parceiro_dashboard_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('parceiro_dashboard'))
        self.assertEqual(resp.status_code, 302)

    # --- Views que expunham dados sem autenticação --------------------------

    def test_fichas_cadastradas_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('fichas_cadastradas'))
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_pesquisa_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('dashboard_pesquisa'))
        self.assertEqual(resp.status_code, 302)

    def test_fotografo_dashboard_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('fotografo_dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_api_dashboard_coordenador_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('api_dashboard_coordenador'))
        self.assertEqual(resp.status_code, 302)

    # --- Comportamento para usuário logado não pode mudar -------------------

    def test_dashboard_logado_gestor_renderiza_200(self):
        gestor = Usuario.objects.create(username='gestor_teste', role='gestor')
        gestor.set_password('senha12345')
        gestor.save()
        self.assertTrue(self.client.login(username='gestor_teste', password='senha12345'))
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_inteligente_logado_gestor_redireciona_dashboard(self):
        Usuario.objects.create(username='gestor_teste2', role='gestor')
        self.client.force_login(Usuario.objects.get(username='gestor_teste2'))
        resp = self.client.get(reverse('dashboard_inteligente'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('dashboard'))

