from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

import io
import os
from PIL import Image

from gestcaptur.models import Evento
from gestcaptur.utils.imagens import processar_selfie

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


class FormandoSelfiePageTests(TestCase):
    """
    A página pública de selfie dos formandos (fotoid) deve renderizar contendo
    as melhorias de captura da Fase 1: countdown, modal fullscreen no mobile,
    constraints de alta resolução e captura espelhada sem upscale.
    """

    def test_pagina_selfie_formandos_renderiza_com_melhorias(self):
        evento = Evento.objects.create(
            fot='TESTE-001',
            data='2026-09-08',
            para_selfie=True,
            uuid='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
        )
        url = reverse('formando_selfie_cadastro_uuid', kwargs={'evento_uuid': evento.uuid})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'countdownOverlay')          # countdown 3-2-1
        self.assertContains(resp, 'modal-fullscreen-sm-down')  # modal fullscreen no mobile
        self.assertContains(resp, 'ideal: 1920')               # constraints de alta resolução
        self.assertContains(resp, 'capturarFoto')              # captura em alta resolução sem upscale
        self.assertContains(resp, 'blobCapturado')             # blob guardado em memória (sem sessionStorage)
        self.assertContains(resp, 'flashOverlay')              # flash-iluminação no disparo
        self.assertContains(resp, 'autoCapturaCheck')          # auto-captura opcional (Fase 3)
        self.assertContains(resp, 'takePhoto')                 # foto full-res do hardware (ImageCapture)
        self.assertContains(resp, 'obterMelhorQuadro')         # best-shot: melhor de 5 quadros


class PipelineImagemSelfieTests(TestCase):
    """
    Fase 2: pipeline de imagem no servidor.

    Toda selfie salva (pública, obrigatória e formandos) passa por
    gestcaptur.utils.imagens.processar_selfie: EXIF-rotate, máx 1200px
    (Lanczos, nunca amplia), autocontraste suave e JPEG otimizado.
    """

    def _jpeg_bytes(self, largura=800, altura=600):
        img = Image.new('RGB', (largura, altura), (120, 120, 120))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        return buf.getvalue()

    def test_redimensiona_para_maximo_1200(self):
        saida, w, h = processar_selfie(self._jpeg_bytes(2400, 1800))
        self.assertEqual(max(w, h), 1200)
        img = Image.open(io.BytesIO(saida))
        self.assertEqual(img.format, 'JPEG')
        self.assertEqual(img.mode, 'RGB')

    def test_nao_amplia_imagem_pequena(self):
        saida, w, h = processar_selfie(self._jpeg_bytes(640, 480))
        self.assertEqual((w, h), (640, 480))

    def test_exif_rotaciona_imagem(self):
        # Foto 800x400 com EXIF Orientation=6 deve sair em retrato (400x800)
        img = Image.new('RGB', (800, 400), (120, 120, 120))
        exif = img.getexif()
        exif[0x0112] = 6
        buf = io.BytesIO()
        img.save(buf, format='JPEG', exif=exif.tobytes())
        saida, w, h = processar_selfie(buf.getvalue())
        self.assertEqual((w, h), (400, 800))

    def test_selfie_formando_salva_jpeg_otimizado(self):
        """Integração: POST etapa=selfie grava o temp já processado (≤1200px)."""
        evento = Evento.objects.create(
            fot='TESTE-002',
            data='2026-09-08',
            para_selfie=True,
            uuid='bbbbbbbb-1111-2222-3333-444444444444',
        )
        upload = SimpleUploadedFile(
            'selfie.jpg', self._jpeg_bytes(2400, 1800), content_type='image/jpeg'
        )
        url = reverse('formando_selfie_cadastro_uuid', kwargs={'evento_uuid': evento.uuid})
        resp = self.client.post(url, {'etapa': 'selfie', 'foto': upload})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['sucesso'])

        temp_nome = self.client.session['selfie_data']['nome_arquivo']
        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', temp_nome)
        self.assertTrue(os.path.exists(temp_path))
        try:
            with open(temp_path, 'rb') as f:
                img = Image.open(f)
            self.assertEqual(img.format, 'JPEG')
            self.assertLessEqual(max(img.size), 1200)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

