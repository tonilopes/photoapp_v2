from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.text import get_valid_filename

import io
import os
import tempfile
from PIL import Image

from gestcaptur.models import Evento, Aluno, caminho_foto_aluno
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
    as melhorias de captura: countdown, modal fullscreen no mobile, constraints
    de alta resolução, captura espelhada sem upscale e o fluxo automático final
    (1 único burst de 2 fotos ao centralizar, rejeitando rosto de perfil).
    E a Fase 4 (visual): design system (f4-card), stepper e dark mode opcional.
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
        self.assertContains(resp, 'captureFallbackBtn')        # botão manual só se o detector falhar
        self.assertContains(resp, 'btnTentarNovamente')        # recuperação amigável pós-falha
        self.assertContains(resp, 'dePerfil')                  # rejeita rosto de lado (pose)
        self.assertContains(resp, 'takePhoto')                 # foto full-res do hardware (ImageCapture)
        self.assertContains(resp, 'obterMelhorQuadro')         # burst de 2 capturas: escolhe a melhor
        self.assertContains(resp, 'burstFeito')                # 1 único burst por centralização (não repete)
        # Fase 4 — visual público
        self.assertContains(resp, 'fase4_publico.css')         # design system carregado
        self.assertContains(resp, 'fase4_publico.js')          # tema + SW público
        self.assertContains(resp, 'manifest_fotoid.json')      # PWA público
        self.assertContains(resp, 'f4-card')                   # card com identidade Photum
        self.assertContains(resp, 'f4-stepper')                # stepper visual
        self.assertContains(resp, 'f4ThemeBtn')                # toggle claro/escuro (opcional)


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


class CaminhoFotoAlunoTests(TestCase):
    """
    Regressão do erro exibido em produção em 25/09/2026 (fluxo do formando):

      "Erro ao salvar cadastro: Storage can not find an available filename for
       event_photos/26155 25-09-2026 Superior Diversos - FATEC Americana 2026.1
       Prime Colação Oficial/ALEXANDERSON_DE_SOUZA_MODES..." Please make sure
       that the corresponding file field allows sufficient "max_length".

    O codigo_turma do evento é usado como pasta da foto e aceita até 100
    caracteres; somado ao prefixo 'event_photos/' e ao nome do formando, o
    caminho ultrapassava o max_length=100 do ImageField e o Django abortava o
    salvamento com SuspiciousFileOperation (a selfie nunca era gravada).
    """

    CODIGO_TURMA_LONGO = (
        '26155 25-09-2026 Superior Diversos - FATEC Americana 2026.1 '
        'Prime Colação Oficial'
    )

    def setUp(self):
        self.evento = Evento.objects.create(
            fot='TESTE-003',
            data='2026-09-25',
            para_selfie=True,
            uuid='cccccccc-1111-2222-3333-444444444444',
            codigo_turma=self.CODIGO_TURMA_LONGO,
        )

    def _jpeg_bytes(self, largura=40, altura=40):
        img = Image.new('RGB', (largura, altura), (200, 200, 200))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        return buf.getvalue()

    def _aluno(self, nome='ALEXANDERSON DE SOUZA MODESTO'):
        return Aluno(
            evento=self.evento,
            nome=nome,
            cpf='123.456.789-00',
            whatsapp='17999990000',
            codigo_turma=self.evento.codigo_turma,
        )

    def test_salva_selfie_com_codigo_turma_longo(self):
        """Antes do hotfix: SuspiciousFileOperation. Depois: grava normalmente."""
        aluno = self._aluno()
        max_length = Aluno._meta.get_field('foto').max_length
        self.assertGreaterEqual(max_length, 200)

        with tempfile.TemporaryDirectory() as media_root, \
                override_settings(MEDIA_ROOT=media_root):
            # Exatamente como views_formandos._processar_cadastro faz
            caminho_sugerido = aluno.get_nome_arquivo_foto()
            self.assertIn('ALEXANDERSON DE SOUZA MODESTO.JPG', caminho_sugerido)
            self.assertLessEqual(
                len('event_photos/' + caminho_sugerido),
                max_length,
            )

            aluno.foto.save(
                caminho_sugerido,
                ContentFile(self._jpeg_bytes()),
                save=False,
            )

            # O Django aplica get_valid_filename() no nome do arquivo
            # (espaços -> '_'), o que gerava "ALEXANDERSON_DE_SOUZA_MODES1..."
            self.assertTrue(aluno.foto.name.startswith('event_photos/'))
            self.assertTrue(
                aluno.foto.name.endswith(
                    get_valid_filename('ALEXANDERSON DE SOUZA MODESTO.JPG')
                )
            )
            self.assertLessEqual(len(aluno.foto.name), max_length)
            self.assertLessEqual(len(aluno.foto.name), 255)
            self.assertTrue(os.path.exists(os.path.join(media_root, aluno.foto.name)))

            # A pasta da turma é preservada como o gestor definiu
            self.assertIn('Prime Colação Oficial', aluno.foto.name)

            # Persistência completa (como em views_formandos._processar_cadastro)
            aluno.save()
            aluno.refresh_from_db()
            self.assertLessEqual(len(aluno.foto.name), max_length)
            self.assertIn('Prime Colação Oficial', aluno.foto.name)

    def test_segundo_evento_real_tambem_salva(self):
        """
        Caso real 2 (print de 26-09-2026):
          event_photos/26205 26-09-2026 Superior Diversos Insper 26.1 Unific.
          Insper 2026.1 Toy SP Family Day/JOAO_RICARDO_qd4lqzP.JPG

        Pasta de 86 chars + 'JOÃO RICARDO': 13 + 86 + 1 + 11 + 4 = 115 > 100
        (max_length antigo do campo) -> SuspiciousFileOperation.
        """
        self.evento.codigo_turma = (
            '26205 26-09-2026 Superior Diversos Insper 26.1 Unific. '
            'Insper 2026.1 Toy SP Family Day'
        )
        self.evento.save(update_fields=['codigo_turma'])

        aluno = self._aluno(nome='JOÃO RICARDO')
        caminho = 'event_photos/' + aluno.get_nome_arquivo_foto()

        # É exatamente por isso que quebrava antes (max_length era 100)
        self.assertGreater(len(caminho), 100)
        self.assertLessEqual(
            len(caminho), Aluno._meta.get_field('foto').max_length
        )

        with tempfile.TemporaryDirectory() as media_root, \
                override_settings(MEDIA_ROOT=media_root):
            aluno.foto.save(
                aluno.get_nome_arquivo_foto(),
                ContentFile(self._jpeg_bytes()),
                save=False,
            )

            self.assertLessEqual(len(aluno.foto.name), 255)
            self.assertIn('Toy SP Family Day', aluno.foto.name)
            self.assertTrue(
                aluno.foto.name.endswith(
                    get_valid_filename('JOÃO RICARDO.JPG')
                )
            )
            self.assertTrue(os.path.exists(os.path.join(media_root, aluno.foto.name)))

    def test_reatribuicao_de_foto_no_save_usa_caminho_seguro(self):
        """
        Fluxo público/obrigatória: a foto é atribuída ao campo e o override de
        Aluno.save() renomeia para '{codigo_turma}/{NOME}.JPG' — o caminho
        precisa continuar dentro do max_length.
        """
        max_length = Aluno._meta.get_field('foto').max_length

        with tempfile.TemporaryDirectory() as media_root, \
                override_settings(MEDIA_ROOT=media_root):
            aluno = self._aluno()
            aluno.foto = ContentFile(
                self._jpeg_bytes(), name='selfie_1_deadbeef.jpg'
            )
            aluno.save()

            self.assertLessEqual(len(aluno.foto.name), max_length)
            self.assertIn('ALEXANDERSON', aluno.foto.name.upper())
            self.assertTrue(os.path.exists(os.path.join(media_root, aluno.foto.name)))

    def test_caminho_nunca_excede_max_length(self):
        """Pasta longa (100) + nome longo (200) seguem abaixo do max_length."""
        aluno = self._aluno(nome='NOME DE FORMANDO MUITO LONGO ' * 8)
        max_length = Aluno._meta.get_field('foto').max_length
        caminho = caminho_foto_aluno(aluno, aluno.get_nome_arquivo_foto())
        self.assertLessEqual(len(caminho), max_length)
        self.assertTrue(caminho.startswith('event_photos/'))

        # Nome já prefixado não deve duplicar o prefixo
        caminho_prefixado = caminho_foto_aluno(aluno, 'event_photos/x/y.jpg')
        self.assertEqual(caminho_prefixado.count('event_photos/'), 1)

    def test_nome_com_caracteres_invalidos_e_sanitizado(self):
        aluno = self._aluno(nome='JOSE/DA SILVA:TESTE*')
        caminho = caminho_foto_aluno(aluno, aluno.get_nome_arquivo_foto())
        arquivo = os.path.basename(caminho)
        for caractere in ('/', '\\', ':', '*', '?', '"', '<', '>', '|'):
            self.assertNotIn(caractere, arquivo)
        self.assertLessEqual(len(caminho), Aluno._meta.get_field('foto').max_length)

