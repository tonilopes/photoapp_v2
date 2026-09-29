// gestcaptur/static/gestcaptur/js/captura_selfie_modal.js
// Captura de selfie pública em modal (similar ao fotografo)

document.addEventListener('DOMContentLoaded', function() {
  console.log('\n🚀 ========== INICIANDO CAPTURA_SELFIE_MODAL ==========');
  console.log('📱 Script captura_selfie_modal.js carregado');
  console.log('🔍 Verificando elementos DOM...');

  // Configurações
  const CONFIG_SELFIE = {
    width: 900,     // antes 600 — alta resolução (pede 1920x1440 à câmera)
    height: 1200,   // antes 800
    quality: 0.9,   // antes 0.85
    maxSizeKB: 900
  };

  // ===== PACOTE CALIBRAGEM SELFIE (25/09/2026) =====
  // CAUSA: em celulares de FOV largo (ex.: Galaxy S23 Ultra, frontal ~80 graus) o rosto
  // ocupa MENOS largura do quadro. Com FACE_MIN=0.28 o app mandava a mensagem INVERTIDA
  // ("Afaste o rosto" com o rosto pequeno/longe) e o aluno ficava preso: "rosto nao
  // reconhecido", "muito perto" estando longe, sem nunca conseguir capturar/salvar.
  // REVERSAO: apagar este bloco e restaurar FACE_MIN 0.28 / FACE_MAX 0.55 + mensagens antigas.
  console.log('PACOTE CALIBRAGEM SELFIE ativo (25/09/2026)');
  const GUIA = {
    faceMin: 0.16,            // antes 0.28 — faixa realista para camera frontal larga
    faceMax: 0.50,            // antes 0.55
    confiancaDeteccao: 0.45,  // antes 0.65 — rosto mais afastado volta a ser detectado
    gracaManualMs: 12000,     // apos 12s sem enquadramento, libera a captura manual
    retryLeituraMs: 800,      // NotReadableError (tipico Samsung): espera liberar e tenta 1x
    toleranciaCentroX: 0.20,  // antes 0.15
    toleranciaCentroY: 0.22   // antes 0.18
  };
  let gracaAvisada = false;
  let retryLeituraFeito = false;

  // NOVO anti-careta: overlay Analisando + validação de expressão (reversível).
  // Para reverter: apagar este bloco NOVO e as chamadas mostrarAnalise/esconderAnalise.
  let faceLandmarkerNovo = null;   // FaceLandmarker (478 pts: EAR/gaze/boca) — null = segue fluxo antigo
  let importMapaTentado = false;
  function mostrarAnaliseModal(texto) {
    const ov = document.getElementById('analiseOverlay');
    const dt = document.getElementById('analiseDetalhe');
    if (dt && texto) dt.textContent = texto;
    if (ov) { ov.style.display = 'flex'; }
    if (cameraStatus && texto) cameraStatus.innerHTML = '🔍 ' + texto;
    ligarWatchdogAnalise();
  }
  function esconderAnaliseModal() {
    const ov = document.getElementById('analiseOverlay');
    if (ov) { ov.style.display = 'none'; }
    if (janelaAnaliseTimer) { clearTimeout(janelaAnaliseTimer); janelaAnaliseTimer = null; }
  }
  // ===== HOTFIX salvamento (25/09/2026) =====
  // CAUSA RAIZ: o handler do botao "Capturar" chamava pararDeteccaoFacial() — que NUNCA
  // existiu neste arquivo. Isso lancava ReferenceError dentro do handler async, abortando
  // toda a captura: o overlay "Analisando sua foto" ficava preso para sempre e o aluno
  // nao conseguia confirmar/salvar. Reversao: apagar deste comentario ate reabilitarBotaoCapturar().
  let janelaAnaliseTimer = null;
  let tentativasReprovadasModal = 0;
  function pararDeteccaoFacial() {
    try {
      if (faceDetectionFrame) { cancelAnimationFrame(faceDetectionFrame); faceDetectionFrame = null; }
    } catch (e) {}
    faceGuidance.valid = false;
    faceGuidance.available = false;
  }
  function retomarDeteccaoFacial() {
    try {
      const v = document.getElementById('selfie-video');
      if (v && faceDetector && !faceDetectionFrame) {
        faceGuidance.available = true;
        faceGuidance.valid = false;
        faceGuidance.deteccoes = 0;   // PACOTE CALIBRAGEM SELFIE: so reabre o gate apos nova avaliacao
        faceGuidance.erros = 0;
        faceGuidance.inicio = performance.now();
        faceDetectionFrame = requestAnimationFrame(function() { orientarEnquadramento(v); });
      }
    } catch (e) {}
  }
  function reabilitarBotaoCapturar() {
    if (captureBtn) { captureBtn.style.display = 'inline-block'; captureBtn.disabled = false; }
    if (refazerBtn) refazerBtn.style.display = 'none';
    if (confirmarBtn) confirmarBtn.style.display = 'none';
  }
  function ligarWatchdogAnalise() {
    if (janelaAnaliseTimer) clearTimeout(janelaAnaliseTimer);
    janelaAnaliseTimer = setTimeout(function() {
      janelaAnaliseTimer = null;
      esconderAnaliseModal();
      retomarDeteccaoFacial();
      reabilitarBotaoCapturar();
      if (cameraStatus) cameraStatus.innerHTML = '⚠️ A análise demorou demais. Toque em Capturar novamente.';
    }, 20000);
  }
  // PACOTE CALIBRAGEM SELFIE (25/09/2026): o delegate 'GPU' do MediaPipe falha em varios
  // Androids (Adreno/One UI) e, antes, o erro derrubava o loop de orientacao (tela travada,
  // aluno sem conseguir capturar). Agora tenta GPU e cai automaticamente para CPU.
  // REVERSAO: chamar Classe.createFromOptions(fileset, opcoes) direto com delegate: 'GPU'.
  async function criarComDelegateFallback(Classe, fileset, base, opcoes) {
    let ultimoErro = null;
    for (const delegado of ['GPU', 'CPU']) {
      try {
        const instancia = await Classe.createFromOptions(fileset, Object.assign({}, opcoes, {
          baseOptions: Object.assign({}, base, { delegate: delegado })
        }));
        console.log('✅ Detector facial criado (delegate=' + delegado + ')');
        return instancia;
      } catch (e) {
        ultimoErro = e;
        console.warn('⚠️ Detector facial com delegate ' + delegado + ' falhou:', e);
      }
    }
    throw (ultimoErro || new Error('Nao foi possivel criar o detector facial'));
  }

  async function carregarLandmarkerSePreciso() {
    if (faceLandmarkerNovo || importMapaTentado) return faceLandmarkerNovo;
    importMapaTentado = true;
    try {
      if (!window.SelfieValidacao) return null; // sem o JS de validação, segue fluxo antigo
      const vision = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs');
      const { FaceLandmarker, FilesetResolver } = vision;
      const fileset = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
      faceLandmarkerNovo = await criarComDelegateFallback(FaceLandmarker, fileset, {
        modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
      }, {
        runningMode: 'VIDEO',
        numFaces: 2, // >1 = intruso (foto colada)
        minFaceDetectionConfidence: 0.3,
        minFacePresenceConfidence: 0.3
      });
      console.log('✅ [NOVO] FaceLandmarker anti-careta ativo');
    } catch (e) {
      console.warn('[NOVO] Landmarker indisponível, segue fluxo antigo:', e);
      faceLandmarkerNovo = null;
    }
    return faceLandmarkerNovo;
  }
  async function validarExpressaoModal(video) {
    // Retorna [] = OK. Sem landmarker/JS = [] (não bloqueia — fluxo antigo vale).
    try {
      if (!window.SelfieValidacao) return [];
      const lm = await carregarLandmarkerSePreciso();
      if (!lm) return [];
      const res = await lm.detectForVideo(video, performance.now());
      const faces = (res && res.faceLandmarks) || [];
      if (faces.length > 1) return ['Mais de um rosto detectado! Fique sozinho no quadro.'];
      if (!faces.length) return []; // deixa o FaceDetector antigo decidir "sem rosto"
      return window.SelfieValidacao.validarExpressao(faces[0], video.videoWidth || 640, video.videoHeight || 480);
    } catch (e) {
      console.warn('[NOVO] validarExpressao fallback:', e);
      return [];
    }
  }
  async function validarFotoFinalModal(imgElOuCanvas) {
    // Valida o frame capturado (detectForVideo no bitmap final). Score <55 = refazer.
    try {
      if (!window.SelfieValidacao) return { ok: true, motivo: '' };
      const lm = await carregarLandmarkerSePreciso();
      if (!lm) return { ok: true, motivo: '' };
      const bmp = await createImageBitmap(imgElOuCanvas);
      const W = bmp.width, H = bmp.height;
      const res = await lm.detectForVideo(bmp, performance.now());
      const faces = (res && res.faceLandmarks) || [];
      if (bmp.close) bmp.close();
      if (!faces.length) return { ok: false, motivo: 'Nenhum rosto na foto.' };
      if (faces.length > 1) return { ok: false, motivo: 'Mais de um rosto na foto.' };
      const alertas = window.SelfieValidacao.validarExpressao(faces[0], W, H);
      if (alertas.length) return { ok: false, motivo: alertas[0] };
      const ys = faces[0].map(p => p.y * H);
      const ratio = (Math.max.apply(null, ys) - Math.min.apply(null, ys)) / H;
      if (ratio > 0.62) return { ok: false, motivo: 'Rosto muito perto — afaste-se (~um braço).' };
      if (ratio < 0.22) return { ok: false, motivo: 'Rosto muito longe — aproxime-se.' };
      return { ok: true, motivo: '' };
    } catch (e) {
      console.warn('[NOVO] validarFotoFinal fallback (aprova):', e);
      return { ok: true, motivo: '' };
    }
  }

  let imagemCapturada = null;
  let streamAtivo = null;
  let eventoId = null;
  let alunoId = null;
  let faceDetector = null;
  let faceDetectionFrame = null;
  // PACOTE CALIBRAGEM SELFIE: deteccoes/erros/inicio permitem saber se o detector
  // REALMENTE avaliou o rosto (o gate do botao "Capturar" so vale se deteccoes > 0) e
  // servem de cronometro para a liberacao manual. Reversao: voltar ao objeto antigo.
  let faceGuidance = { available: false, valid: false, deteccoes: 0, erros: 0, inicio: 0 };
  let ultimoAvisoFalado = '';
  let qualidadeAtual = { brilho: 'ok', nitidez: 'ok' };
  let ultimaAvaliacaoQualidade = 0;
  let analiseCanvas = null;
  let analiseCtx = null;

  // Avalia brilho médio e nitidez (desfoque) de um frame do vídeo via canvas
  function avaliarQualidadeImagem(video) {
    const SAMPLE_W = 96, SAMPLE_H = 96;
    if (!analiseCanvas) {
      analiseCanvas = document.createElement('canvas');
      analiseCanvas.width = SAMPLE_W;
      analiseCanvas.height = SAMPLE_H;
      analiseCtx = analiseCanvas.getContext('2d', { willReadFrequently: true });
    }
    analiseCtx.drawImage(video, 0, 0, SAMPLE_W, SAMPLE_H);
    const { data } = analiseCtx.getImageData(0, 0, SAMPLE_W, SAMPLE_H);

    const gray = new Float32Array(SAMPLE_W * SAMPLE_H);
    let somaBrilho = 0;
    for (let i = 0, p = 0; i < data.length; i += 4, p++) {
      const l = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      gray[p] = l;
      somaBrilho += l;
    }
    const brilhoMedio = somaBrilho / gray.length;

    // Variância do Laplaciano (medida clássica de nitidez): baixo valor = imagem borrada
    let somaGrad = 0, somaGrad2 = 0, n = 0;
    for (let y = 1; y < SAMPLE_H - 1; y++) {
      for (let x = 1; x < SAMPLE_W - 1; x++) {
        const idx = y * SAMPLE_W + x;
        const lap = (gray[idx - 1] + gray[idx + 1] + gray[idx - SAMPLE_W] + gray[idx + SAMPLE_W]) - 4 * gray[idx];
        somaGrad += lap;
        somaGrad2 += lap * lap;
        n++;
      }
    }
    const media = somaGrad / n;
    const variancia = (somaGrad2 / n) - (media * media);

    return {
      brilho: brilhoMedio < 55 ? 'escuro' : brilhoMedio > 205 ? 'claro' : 'ok',
      nitidez: variancia < 12 ? 'borrado' : 'ok'
    };
  }

  // Elementos do modal
  const cameraArea = document.getElementById('camera-area');
  const captureBtn = document.getElementById('btn-capturar-modal');
  const refazerBtn = document.getElementById('btn-refazer-modal');
  const confirmarBtn = document.getElementById('btn-confirmar-modal');
  const cameraModal = document.getElementById('cameraModal');
  const cameraStatus = document.getElementById('camera-status');

  console.log('✅ camera-area:', cameraArea ? 'ENCONTRADO' : '❌ NÃO ENCONTRADO');
  console.log('✅ btn-capturar-modal:', captureBtn ? 'ENCONTRADO' : '❌ NÃO ENCONTRADO');
  console.log('✅ btn-refazer-modal:', refazerBtn ? 'ENCONTRADO' : '❌ NÃO ENCONTRADO');
  console.log('✅ btn-confirmar-modal:', confirmarBtn ? 'ENCONTRADO' : '❌ NÃO ENCONTRADO');
  console.log('✅ cameraModal:', cameraModal ? 'ENCONTRADO' : '❌ NÃO ENCONTRADO');
  console.log('✅ camera-status:', cameraStatus ? 'ENCONTRADO' : '❌ NÃO ENCONTRADO');

  if (!cameraModal) {
    console.error('❌ ERRO CRÍTICO: Modal #cameraModal não encontrado!');
    alert('Erro ao carregar interface. Recarregue a página.');
    return;
  }

  // PROTEÇÃO: Garantir que #camera-area começa VAZIO
  if (cameraArea) {
    console.log('🧹 Limpando #camera-area (removendo qualquer elemento anterior)');
    cameraArea.innerHTML = '';
    cameraArea.style.background = '#000';
    // Observar adições inesperadas (outros scripts) e remover vídeos não autorizados
    try {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
          mutation.addedNodes.forEach(node => {
            if (node && node.tagName && node.tagName.toLowerCase() === 'video') {
              const modalShown = cameraModal && cameraModal.classList.contains('show');
              console.log('🔎 MutationObserver: vídeo adicionado ao #camera-area, modalShown=', modalShown);
              if (!modalShown) {
                console.log('🧹 Removendo vídeo adicionado fora do modal');
                try {
                  if (node.srcObject && node.srcObject.getTracks) {
                    node.srcObject.getTracks().forEach(t => { try { t.stop(); } catch(e){} });
                  }
                } catch(e) { console.warn('erro ao parar tracks:', e); }
                node.remove();
              }
            }
          });
        });
      });
      observer.observe(cameraArea, { childList: true, subtree: true });
      // armazenar no window para possível inspeção
      window._selfieMutationObserver = observer;
    } catch (e) {
      console.warn('MutationObserver não disponível:', e);
    }
  }

  // Extrair evento_id do data-attribute ou URL
  function extrairEventoId() {
    const element = document.querySelector('[data-evento-id]');
    if (element) {
      const id = element.dataset.eventoId;
      console.log('📍 Evento ID extraído de data-attribute:', id);
      return id;
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('evento_id');
    if (id) console.log('📍 Evento ID extraído de URL:', id);
    return id || null;
  }

  eventoId = extrairEventoId();
  console.log('📍 Final Evento ID:', eventoId);

  function falarAviso(mensagem) {
    if (!('speechSynthesis' in window) || mensagem === ultimoAvisoFalado) return;
    ultimoAvisoFalado = mensagem;
    window.speechSynthesis.cancel();
    const fala = new SpeechSynthesisUtterance(mensagem);
    fala.lang = 'pt-BR';
    fala.rate = 1;
    window.speechSynthesis.speak(fala);
  }

  async function iniciarOrientacaoFacial(video) {
    try {
      const vision = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22/+esm');
      const fileset = await vision.FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22/wasm'
      );
      faceDetector = await criarComDelegateFallback(vision.FaceDetector, fileset, {
        modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
      }, {
        runningMode: 'VIDEO',
        minDetectionConfidence: GUIA.confiancaDeteccao
      });
      faceGuidance.available = true;
      faceGuidance.deteccoes = 0;
      faceGuidance.erros = 0;
      faceGuidance.inicio = performance.now();
      orientarEnquadramento(video);
    } catch (error) {
      console.warn('Orientação facial indisponível:', error);
      faceGuidance.available = false;
      faceGuidance.deteccoes = 0;   // PACOTE CALIBRAGEM SELFIE: sem detector, captura manual livre
      atualizarStatus('Câmera pronta. Toque em Capturar quando estiver enquadrado.', false);
    }
  }

  function atualizarStatus(mensagem, falar = true) {
    if (cameraStatus) cameraStatus.textContent = mensagem;
    if (falar) falarAviso(mensagem.replace(/[📷✅⚠️❌]/g, '').trim());
    // Sincroniza cor do oval com validade do enquadramento
    try {
      const oval = document.getElementById('selfie-oval');
      if (oval) oval.classList.toggle('ok', faceGuidance.valid === true);
    } catch (e) {}
  }

  // ===== PACOTE CALIBRAGEM SELFIE (25/09/2026): o loop de orientacao NUNCA pode morrer =====
  // CAUSA: se o video ainda nao tinha imagem (camera frontal "fria", comum nos Samsung) ou
  // se o detectForVideo lancava excecao (delegate GPU), a funcao saia SEM reagendar o
  // requestAnimationFrame. Resultado: available=true + valid=false PARA SEMPRE e o gate do
  // botao "Capturar" travava o aluno definitivamente ("rosto nao reconhecido", "muito
  // perto/longe" em loop, sem conseguir salvar).
  // REVERSAO: apagar o wrapper e voltar a funcao unica com "if (!faceDetector || video.readyState < 2) return;".
  function liberarCapturaManual() {
    if (gracaAvisada) return;
    gracaAvisada = true;
    if (cameraStatus) cameraStatus.innerHTML = '📷 Você pode tocar em Capturar a qualquer momento — cuidamos da qualidade depois.';
    if (navigator.vibrate) navigator.vibrate(80);
  }

  function orientarEnquadramento(video) {
    try {
      orientarEnquadramentoInterno(video);
    } catch (e) {
      faceGuidance.erros += 1;
      console.warn('orientarEnquadramento erro #' + faceGuidance.erros + ':', e);
      if (faceGuidance.erros >= 5) {
        faceGuidance.available = false;   // nao gateia mais: o aluno captura manualmente
        atualizarStatus('Enquadramento automático indisponível. Toque em Capturar.', false);
      }
    } finally {
      if (!faceGuidance.valid && faceGuidance.deteccoes > 0 &&
          (performance.now() - faceGuidance.inicio) > GUIA.gracaManualMs) {
        liberarCapturaManual();
      }
      faceDetectionFrame = (faceGuidance.available && faceGuidance.erros < 5)
        ? requestAnimationFrame(function() { orientarEnquadramento(video); })
        : null;
    }
  }

  function orientarEnquadramentoInterno(video) {
    if (!faceDetector) return;                                         // sem detector: nao gateia
    if (!video || video.readyState < 2 || !video.videoWidth) return;    // camera aquecendo: reagenda
    const resultado = faceDetector.detectForVideo(video, performance.now());
    const faces = (resultado && resultado.detections) || [];
    faceGuidance.deteccoes += 1;
    faceGuidance.valid = false;

    if (faces.length === 0) {
      atualizarStatus('Não encontrei o rosto. Aproxime um pouco e olhe para a câmera.');
    } else if (faces.length > 1) {
      atualizarStatus('Deixe apenas uma pessoa na frente da câmera.');
    } else {
      const box = faces[0].boundingBox;
      const centerX = box.originX + box.width / 2;
      const centerY = box.originY + box.height / 2;
      const centered = Math.abs(centerX - video.videoWidth / 2) < video.videoWidth * GUIA.toleranciaCentroX &&
        Math.abs(centerY - video.videoHeight / 2) < video.videoHeight * GUIA.toleranciaCentroY;
      // FAIXA REALISTA DE DISTANCIA: com FACE_MIN 0.28 o rosto tinha de ficar colado na
      // camera e, quando ele estava PEQUENO/longe, a mensagem mandava AFASTAR — o aluno ia
      // para o lado errado e nunca passava no enquadramento. Reversao: FACE_MIN 0.28 / FACE_MAX 0.55.
      const largura = box.width / video.videoWidth;
      const goodSize = largura > GUIA.faceMin && largura < GUIA.faceMax;

      if (!centered) {
        atualizarStatus('Centralize o rosto no oval da tela.');
      } else if (largura <= GUIA.faceMin) {
        atualizarStatus('Aproxime um pouco o rosto: ele está pequeno dentro do oval.');
      } else if (largura >= GUIA.faceMax) {
        atualizarStatus('Afaste um pouco o rosto: ele está maior que o oval.');
      } else if (!goodSize) {
        atualizarStatus('Ajuste a distância até o rosto caber no oval.');
      } else {
        const agora = performance.now();
        if (agora - ultimaAvaliacaoQualidade > 350) {
          ultimaAvaliacaoQualidade = agora;
          qualidadeAtual = avaliarQualidadeImagem(video);
        }
        if (qualidadeAtual.brilho === 'escuro') {
          atualizarStatus('Muito escuro. Procure um local mais iluminado.');
        } else if (qualidadeAtual.brilho === 'claro') {
          atualizarStatus('Muita luz direta. Evite luz forte atrás ou de frente pra câmera.');
        } else if (qualidadeAtual.nitidez === 'borrado') {
          atualizarStatus('Imagem borrada. Segure o celular firme e aguarde o foco.');
        } else {
          faceGuidance.valid = true;
          atualizarStatus('Rosto bem enquadrado. Você pode capturar.', false);
        }
      }
    }
    // PACOTE CALIBRAGEM SELFIE: o reagendamento do requestAnimationFrame passou a ser feito
    // pelo wrapper orientarEnquadramento() (bloco finally) — assim o loop nunca fica sem a
    // proxima volta, mesmo quando o video ainda esta aquecendo ou o detector falha.
  }

  // EVENT: Modal aberto
  if (cameraModal) {
    cameraModal.addEventListener('shown.bs.modal', function() {
      console.log('\n📺 ========== MODAL ABERTO ==========');
      console.log('🎬 evento "shown.bs.modal" disparado');
      console.log('🧹 Limpando #camera-area antes de inicializar');
      
      // IMPORTANTE: Limpar #camera-area para evitar elementos antigos
      if (cameraArea) {
        cameraArea.innerHTML = '';
      }
      
      // Delay para garantir que modal está totalmente renderizado
      setTimeout(() => {
        console.log('⏳ Chamando inicializarCamera() após 500ms');
        inicializarCamera();
      }, 500);
    });
  }

  // EVENT: Modal fechado
  if (cameraModal) {
    cameraModal.addEventListener('hidden.bs.modal', function() {
      console.log('\n📺 ========== MODAL FECHADO ==========');
      console.log('🎬 evento "hidden.bs.modal" disparado');
      // HOTFIX salvamento: limpa overlay/contador ao fechar (reversao: apagar estas 2 linhas)
      if (typeof esconderAnaliseModal === 'function') esconderAnaliseModal();
      tentativasReprovadasModal = 0;
      pararDeteccaoFacial();   // PACOTE CALIBRAGEM SELFIE: encerra o loop de orientacao ao fechar
      pararCamera();
    });
  }

  // ===== PACOTE CALIBRAGEM SELFIE (25/09/2026): PLANO B universal =====
  // Cobre os casos em que a API de camera nao pode ser usada no aparelho/navegador do aluno:
  // webview de WhatsApp/Instagram (sem navigator.mediaDevices), permissao negada, camera
  // ocupada por outro app (NotReadableError, tipico da Samsung) ou falha de GPU.
  // Usa a camera NATIVA pelo <input capture="user"> e entra no MESMO fluxo de
  // preview/confirmar/salvar (o servidor recebe o mesmo JPEG base64).
  // REVERSAO: apagar esta funcao e as chamadas oferecerCapturaPorArquivo().
  function oferecerCapturaPorArquivo(motivo) {
    try {
      let entrada = document.getElementById('selfie-arquivo-fallback');
      if (!entrada) {
        entrada = document.createElement('input');
        entrada.type = 'file';
        entrada.id = 'selfie-arquivo-fallback';
        entrada.accept = 'image/*';
        entrada.setAttribute('capture', 'user');
        entrada.style.display = 'none';
        entrada.addEventListener('change', function() {
          const arquivo = entrada.files && entrada.files[0];
          if (!arquivo) return;
          if (cameraStatus) cameraStatus.innerHTML = '⏳ Preparando sua foto...';
          const leitor = new FileReader();
          leitor.onload = function() {
            const aux = new Image();
            aux.onload = function() {
              const cv = document.createElement('canvas');
              cv.width = CONFIG_SELFIE.width;
              cv.height = CONFIG_SELFIE.height;
              const c2 = cv.getContext('2d');
              const escala = Math.max(cv.width / aux.width, cv.height / aux.height);
              const lw = aux.width * escala, lh = aux.height * escala;
              c2.drawImage(aux, (cv.width - lw) / 2, (cv.height - lh) / 2, lw, lh);
              imagemCapturada = cv.toDataURL('image/jpeg', CONFIG_SELFIE.quality);
              esconderAnaliseModal();
              mostrarTelaPreview(false);   // foto do celular ja vem como o aluno ve
            };
            aux.onerror = function() { alert('Não foi possível ler a foto escolhida. Tente de novo.'); };
            aux.src = leitor.result;
          };
          leitor.onerror = function() { alert('Não foi possível ler a foto escolhida. Tente de novo.'); };
          leitor.readAsDataURL(arquivo);
        });
        document.body.appendChild(entrada);
      }

      let botao = document.getElementById('btn-selfie-arquivo');
      if (!botao) {
        botao = document.createElement('button');
        botao.type = 'button';
        botao.id = 'btn-selfie-arquivo';
        botao.className = 'btn btn-warning btn-lg mt-2';
        botao.innerHTML = '📱 Usar a câmera do celular';
        botao.addEventListener('click', function() { entrada.click(); });
        const alvo = (captureBtn && captureBtn.parentNode) ? captureBtn.parentNode : document.body;
        alvo.appendChild(botao);
      }
      botao.style.display = 'inline-block';

      if (cameraStatus) {
        cameraStatus.innerHTML = '📱 ' + (motivo || 'Vamos usar a câmera do seu celular.')
          + ' Toque em "Usar a câmera do celular".';
      }
      try { entrada.click(); } catch (e) { console.warn('clique automatico bloqueado:', e); }
    } catch (e) {
      console.warn('Fallback de arquivo indisponivel:', e);
    }
  }

  // ================== PARAR CÂMERA ==================
  function pararCamera() {
    console.log('🛑 Parando câmera...');
    
    // Parar video element
    const video = document.getElementById('selfie-video');
    if (video) {
      video.srcObject = null;
      console.log('  - video.srcObject = null');
    }
    
    // Parar todos os tracks do stream
    if (streamAtivo) {
      streamAtivo.getTracks().forEach(track => {
        console.log('  - Stopping ' + track.kind + ' track:', track.label);
        track.stop();
      });
      streamAtivo = null;
      console.log('✅ Câmera parada com sucesso');
    } else {
      console.log('ℹ️  Nenhum stream ativo para parar');
    }
  }

  // ================== INICIALIZAR CÂMERA ==================
  function inicializarCamera() {
    console.log('\n' + '='.repeat(70));
    console.log('📷 INICIALIZANDO CÂMERA - INÍCIO');
    console.log('='.repeat(70));
    console.log('🌐 Informações da página:');
    console.log('  - URL:', window.location.href);
    console.log('  - Protocolo:', window.location.protocol);
    console.log('  - Host:', window.location.host);
    console.log('  - Is localhost:', window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
    
    // CRÍTICO: Parar câmera anterior se existir
    console.log('\n🔌 Verificando se há câmera anterior ativa...');
    if (streamAtivo) {
      console.log('⚠️  Stream anterior encontrado - parando primeiro');
      pararCamera();
      // Pequeno delay para liberar recursos
      setTimeout(() => {
        continuarInicializacao();
      }, 300);
      return;
    }
    
    continuarInicializacao();
  }

  function continuarInicializacao() {
    retryLeituraFeito = false;   // PACOTE CALIBRAGEM SELFIE: cada abertura pode tentar de novo
    console.log('\n[1/6] 🔍 Verificando suporte a getUserMedia...');
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.error('❌ getUserMedia NÃO DISPONÍVEL - Browser não suporta');
      if (cameraStatus) cameraStatus.innerHTML = '❌ Este navegador não libera a câmera (comum em links abertos dentro do WhatsApp/Instagram).';
      alert('Este navegador não libera a câmera — comum em links abertos dentro do WhatsApp ou Instagram.\n\nVamos usar a câmera do seu celular.');
      oferecerCapturaPorArquivo('Este navegador não libera a câmera.');
      return;
    }
    console.log('✅ getUserMedia disponível');

    // Verificação 2: elemento camera-area
    console.log('\n[2/6] 🔍 Verificando elemento #camera-area...');
    if (!cameraArea) {
      console.error('❌ #camera-area NÃO ENCONTRADO');
      if (cameraStatus) cameraStatus.innerHTML = '❌ Elemento de câmera não encontrado';
      return;
    }
    console.log('✅ #camera-area encontrado');

    // Etapa 3: Limpar e criar elemento video
    console.log('\n[3/6] 🎥 Criando elemento <video>...');
    cameraArea.innerHTML = '';

    const video = document.createElement('video');
    video.id = 'selfie-video';
    video.setAttribute('playsinline', 'true');
    video.setAttribute('muted', 'true');
    video.setAttribute('webkit-playsinline', 'true');
    
    Object.assign(video.style, {
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      transform: 'scaleX(-1)',
      borderRadius: '8px',
      backgroundColor: '#000',
      display: 'block'
    });

    cameraArea.appendChild(video);
    // Oval de enquadramento MENOR (visual): guia o formando a manter distância
    if (!cameraArea.querySelector('.selfie-oval')) {
      const oval = document.createElement('div');
      oval.className = 'selfie-oval';
      oval.id = 'selfie-oval';
      oval.setAttribute('aria-hidden', 'true');
      cameraArea.appendChild(oval);
      const hint = document.createElement('div');
      hint.className = 'selfie-oval-hint';
      hint.textContent = '↔️ Afaste o rosto até caber no oval';
      hint.setAttribute('aria-hidden', 'true');
      cameraArea.appendChild(hint);
    }
    console.log('✅ <video id="selfie-video"> criado e adicionado ao DOM');

    // Etapa 4: Atualizar status
    console.log('\n[4/6] 📢 Atualizando mensagem de status...');
    if (cameraStatus) cameraStatus.innerHTML = '⏳ Pedindo permissão para câmera...';
    console.log('✅ Status atualizado');

    // Etapa 5: Chamar getUserMedia
    console.log('\n[5/6] 📞 Chamando navigator.mediaDevices.getUserMedia...');
    const constraints = {
      video: {
        facingMode: 'user',
        width: { ideal: CONFIG_SELFIE.width },
        height: { ideal: CONFIG_SELFIE.height }
      },
      audio: false
    };
    console.log('  Constraints:', JSON.stringify(constraints, null, 2));

    // Função para tentar com constraints progressivamente menos restritivos
    function tentarGetUserMedia(tentativa = 1) {
      console.log(`\n📞 Tentativa ${tentativa} de getUserMedia...`);

      navigator.mediaDevices.getUserMedia(constraints)
        .then(stream => {
          console.log('\n✅✅✅ getUserMedia SUCESSO! ✅✅✅');
          console.log('📊 Stream recebido:');
          console.log('  - Total de tracks:', stream.getTracks().length);
          
          const videoTrack = stream.getVideoTracks()[0];
          if (videoTrack) {
            const settings = videoTrack.getSettings();
            console.log('  - Video track settings:');
            console.log('    * width:', settings.width);
            console.log('    * height:', settings.height);
          console.log('    * facingMode:', settings.facingMode);
        }

        // Atribuir stream
        console.log('\n[6/6] 🔗 Atribuindo stream ao elemento video...');
        streamAtivo = stream;
        video.srcObject = stream;
        console.log('✅ video.srcObject = stream');

        // Atualizar status
        if (cameraStatus) cameraStatus.innerHTML = '⏳ Iniciando transmissão de vídeo...';

        // Event listeners
        console.log('\n📡 Configurando event listeners...');

        video.addEventListener('play', function() {
          console.log('✅ ▶️  Video PLAY event disparado');
          console.log('  - videoWidth:', video.videoWidth);
          console.log('  - videoHeight:', video.videoHeight);
          console.log('  - readyState:', video.readyState);
          console.log('  - paused:', video.paused);
          atualizarStatus('Carregando orientação facial...', false);
          iniciarOrientacaoFacial(video);
        }, { once: false });

        video.addEventListener('canplay', function() {
          console.log('✅ Video CANPLAY event disparado');
          console.log('  - videoWidth:', video.videoWidth);
          console.log('  - videoHeight:', video.videoHeight);
          console.log('  - readyState:', video.readyState);
          console.log('  - Chamando video.play()...');
          
          video.play()
            .then(() => {
              console.log('✅ video.play() chamado com sucesso');
            })
            .catch(err => {
              console.error('❌ video.play() erro:', err.name, '-', err.message);
            });
        }, { once: false });

        video.addEventListener('loadedmetadata', function() {
          console.log('✅ Video LOADEDMETADATA event disparado');
          console.log('  - videoWidth:', video.videoWidth);
          console.log('  - videoHeight:', video.videoHeight);
        }, { once: false });

        video.addEventListener('error', function(e) {
          console.error('❌ Video ERROR event:', e);
          if (cameraStatus) cameraStatus.innerHTML = '❌ Erro ao reproduzir vídeo';
        });

        // Timeout safety check
        console.log('\n⏱️  Configurando timeout safety check (5 segundos)...');
        setTimeout(() => {
          console.log('\n⏱️  [TIMEOUT 5s] Verificando estado do video...');
          console.log('  - videoWidth:', video.videoWidth);
          console.log('  - videoHeight:', video.videoHeight);
          console.log('  - readyState:', video.readyState, `(${['HAVE_NOTHING', 'HAVE_METADATA', 'HAVE_CURRENT_DATA', 'HAVE_FUTURE_DATA', 'HAVE_ENOUGH_DATA'][video.readyState] || 'UNKNOWN'})`);
          console.log('  - paused:', video.paused);
          console.log('  - stream.active:', streamAtivo?.active);

          if (video.videoWidth > 0 && video.videoHeight > 0 && video.paused) {
            console.log('⚠️  Video inicializado mas em PAUSA - tentando play()...');
            if (cameraStatus) cameraStatus.innerHTML = '⏳ Recuperando transmissão...';
            
            video.play()
              .then(() => {
                console.log('✅ Manual play() chamado com sucesso');
                if (cameraStatus) cameraStatus.innerHTML = '✅ Câmera pronta - clique em "Capturar"';
              })
              .catch(err => {
                console.error('❌ Manual play() erro:', err);
              });
          } else if (video.videoWidth === 0 || video.videoHeight === 0) {
            console.warn('⚠️  video.videoWidth ou videoHeight ainda é 0');
            console.warn('⚠️  A câmera pode estar levando mais tempo...');
          } else if (!video.paused) {
            console.log('✅ Video está rodando (não pausado)');
          }
        }, 5000);

        console.log('\n' + '='.repeat(70));
        console.log('📷 INICIALIZAÇÃO COMPLETA - Video pronto para uso');
        console.log('='.repeat(70) + '\n');
      })
      .catch(err => {
        console.error('\n❌ Tentativa ' + tentativa + ' FALHOU');
        console.error('  - err.name:', err.name);
        console.error('  - err.message:', err.message);

        // Se for erro de constraint, tentar com constraints menos restritivos
        if (err.name === 'OverconstrainedError' && tentativa < 3) {
          console.warn('⚠️  OverconstrainedError - tentando com constraints menos restritivos...');
          
          if (tentativa === 1) {
            // Tentar 2: remover height/width specifics
            constraints.video = { facingMode: 'user' };
            tentarGetUserMedia(2);
            return;
          } else if (tentativa === 2) {
            // Tentar 3: remover facingMode
            constraints.video = true;
            tentarGetUserMedia(3);
            return;
          }
        }

        // PACOTE CALIBRAGEM SELFIE: NotReadableError ("Could not start video source") e o
        // erro mais comum nos Galaxys — a camera ainda esta presa por outro app/aba e libera
        // em menos de 1 segundo. Antes o aluno caia direto no erro.
        // REVERSAO: apagar este bloco.
        if (err.name === 'NotReadableError' && !retryLeituraFeito) {
          retryLeituraFeito = true;
          console.warn('⚠️  Câmera ocupada — aguardando liberação e tentando novamente...');
          if (cameraStatus) cameraStatus.innerHTML = '⏳ Liberando a câmera (feche outros apps que usam a câmera)...';
          setTimeout(function() { tentarGetUserMedia(1); }, GUIA.retryLeituraMs);
          return;
        }

        // Se chegou aqui, falhou de verdade
        console.error('\n❌❌❌ getUserMedia ERRO CRÍTICO ❌❌❌');
        console.error('  - err.name:', err.name);
        console.error('  - err.message:', err.message);
        console.error('  - err.code:', err.code);
        if (err.stack) console.error('  - Stack:', err.stack);

        let mensagem = '❌ Erro ao acessar câmera';

        if (err.name === 'NotAllowedError') {
          mensagem = '🔒 Permissão negada. Vá em Configurações > Privacidade > Câmera e autorize.';
        } else if (err.name === 'NotFoundError') {
          mensagem = '📷 Câmera não encontrada neste dispositivo.';
        } else if (err.name === 'NotReadableError') {
          mensagem = '⚠️  Câmera está em uso por outro app. Feche e tente novamente.';
        } else if (err.name === 'SecurityError') {
          const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
          if (isLocalhost) {
            mensagem = '🔐 SecurityError local - verifique permissões do SO. Tente: chrome://flags -> #unsafely-treat-insecure-origin-as-secure';
          } else {
            mensagem = '🔐 Use HTTPS ou localhost para acessar câmera.';
          }
        } else if (err.name === 'OverconstrainedError') {
          mensagem = '⚙️  Câmera não atende aos requisitos (all 3 attempts).';
        }

        console.error('Mensagem para usuário:', mensagem);
        if (cameraStatus) {
          cameraStatus.innerHTML = mensagem + ' Use o botão "Usar a câmera do celular".';
          cameraStatus.style.color = '#ff6b6b';
        }
        alert(mensagem + '\n\nDá para tirar a selfie com a câmera do próprio celular: toque em "Usar a câmera do celular".');
        oferecerCapturaPorArquivo(mensagem);

        console.log('\n' + '='.repeat(70));
        console.log('❌ INICIALIZAÇÃO FALHOU');
        console.log('='.repeat(70) + '\n');
      });
    } // Fim da função tentarGetUserMedia

    // Chamar primeira tentativa
    tentarGetUserMedia(1);
  }

  // ================== CAPTURAR FOTO ==================
  if (captureBtn) {
    captureBtn.addEventListener('click', async function() {
      console.log('\n📸 CAPTURANDO FOTO');

      const video = document.getElementById('selfie-video');
      if (!video || !streamAtivo) {
        alert('❌ Câmera não está disponível');
        console.error('❌ Video não encontrado ou stream inativo');
        return;
      }

      // PACOTE CALIBRAGEM SELFIE: o gate so vale se o detector REALMENTE ja avaliou o rosto
      // (deteccoes > 0) e ainda dentro da janela de 12s; depois disso o aluno SEMPRE consegue
      // capturar (a validacao da foto final continua valendo).
      // REVERSAO: voltar a usar apenas "if (faceGuidance.available && !faceGuidance.valid)".
      const guiaAtiva = faceGuidance.available === true && faceGuidance.deteccoes > 0;
      const guiaVencida = (performance.now() - faceGuidance.inicio) > GUIA.gracaManualMs;
      if (guiaAtiva && !faceGuidance.valid && !guiaVencida) {
        const aviso = (cameraStatus && cameraStatus.textContent)
          ? cameraStatus.textContent
          : 'Ajuste o rosto no oval da tela.';
        atualizarStatus(aviso + ' (ou aguarde alguns segundos e toque em Capturar).');
        return;
      }

      console.log('✅ Video element encontrado');

      // NOVO: fecha a captura e mostra "Analisando sua foto, um momento"
      if (captureBtn) captureBtn.disabled = true;   // HOTFIX: evita clique duplo durante a analise
      mostrarAnaliseModal('Analisando sua foto, um momento...');
      pararDeteccaoFacial();
      const motivos = [];
      // 1) expressão/olhos/boca/distância/intruso no frame ao vivo (não bloqueia se landmarker falhar)
      try {
        const alertasAoVivo = await validarExpressaoModal(video);
        if (alertasAoVivo.length) motivos.push(alertasAoVivo[0]);
      } catch (e) {}
      // 2) qualidade (brilho/nitidez) — fluxo antigo
      try {
        const q = avaliarQualidadeImagem(video);
        if (q.brilho !== 'ok') motivos.push(q.brilho === 'escuro' ? 'Foto escura — melhore a iluminação.' : 'Claro demais — evite contraluz.');
        if (q.nitidez !== 'ok') motivos.push('Foto tremida/embaçada — segure firme.');
      } catch (e) {}

      // PACOTE CALIBRAGEM SELFIE: a camera frontal "fria" (comum nos Samsung) pode ainda
      // nao ter quadro — antes isso gerava foto preta ou esticada.
      // REVERSAO: apagar a verificacao e voltar ao drawImage esticado.
      if (!video.videoWidth || !video.videoHeight) {
        esconderAnaliseModal();
        retomarDeteccaoFacial();
        reabilitarBotaoCapturar();
        atualizarStatus('A câmera ainda está iniciando. Aguarde 1 segundo e toque em Capturar novamente.');
        return;
      }

      // Canvas para captura
      const canvas = document.createElement('canvas');
      canvas.width = CONFIG_SELFIE.width;
      canvas.height = CONFIG_SELFIE.height;

      // Recorte central (equivalente a object-fit: cover) em vez de esticar o quadro
      // 16:9 dentro de 3:4: mantem a proporcao do rosto (antes ele saia achatado).
      const ctx = canvas.getContext('2d');
      const escalaCapa = Math.max(CONFIG_SELFIE.width / video.videoWidth, CONFIG_SELFIE.height / video.videoHeight);
      const larguraCapa = video.videoWidth * escalaCapa;
      const alturaCapa = video.videoHeight * escalaCapa;
      ctx.save();
      ctx.translate(CONFIG_SELFIE.width, 0);
      ctx.scale(-1, 1);   // espelha igual ao preview
      ctx.drawImage(video, (CONFIG_SELFIE.width - larguraCapa) / 2, (CONFIG_SELFIE.height - alturaCapa) / 2, larguraCapa, alturaCapa);
      ctx.restore();

      // NOVO: valida a foto final (frame capturado) — careta de último segundo
      try {
        const checkFinal = await validarFotoFinalModal(canvas);
        if (!checkFinal.ok) motivos.push(checkFinal.motivo);
      } catch (e) {}

      // HOTFIX salvamento: reprovacao sem alert() bloqueante e SEM reinicializar a camera
      // (o "await inicializarCamera()" anterior causava double-init/NotReadableError e, como
      // o pararDeteccaoFacial() inexistente abortava o handler, nada disso rodava).
      // Na 3a reprovacao aceita a captura, para ninguem ficar travado sem conseguir salvar.
      // Reversao: voltar ao if (motivos.length) { alert(...); await inicializarCamera(); return; }
      if (motivos.length && tentativasReprovadasModal < 2) {
        tentativasReprovadasModal += 1;
        esconderAnaliseModal();
        retomarDeteccaoFacial();
        reabilitarBotaoCapturar();
        if (cameraStatus) cameraStatus.innerHTML = '⚠️ Você precisa refazer sua foto: ' + motivos[0] + ' Toque em Capturar novamente.';
        if (navigator.vibrate) navigator.vibrate(120);
        return;
      }
      if (motivos.length) {
        tentativasReprovadasModal = 0;
        if (cameraStatus) cameraStatus.innerHTML = '⚠️ Usando a melhor captura: ' + motivos[0];
      } else {
        tentativasReprovadasModal = 0;
      }

      esconderAnaliseModal();
      imagemCapturada = canvas.toDataURL('image/jpeg', CONFIG_SELFIE.quality);
      console.log('✅ Imagem capturada');
      console.log('📊 Tamanho:', imagemCapturada.length, 'bytes');

      // Mostrar preview (só a foto selecionada: [Aprovar/Confirmar] [Fazer outra])
      if (cameraStatus) cameraStatus.innerHTML = '👀 Foto selecionada! Aprove ou tire outra.';
      mostrarTelaPreview();
    });
  }

  // ================== PREVIEW ==================
  function mostrarTelaPreview(espelhar) {
    pararDeteccaoFacial();   // PACOTE CALIBRAGEM SELFIE: nao deixa o loop de orientacao rodando no preview
    console.log('\n🖼️  Mostrando preview da imagem');
    
    // Parar câmera
    pararCamera();

    // Limpar camera-area
    cameraArea.innerHTML = '';

    // Criar img para preview
    const img = document.createElement('img');
    img.src = imagemCapturada;
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.objectFit = 'cover';
    img.style.borderRadius = '8px';
    img.style.transform = (espelhar === false) ? 'none' : 'scaleX(-1)';

    cameraArea.appendChild(img);

    // Atualizar status
    if (cameraStatus) cameraStatus.innerHTML = '👀 Visualize sua selfie. Aprove ou tire outra.';

    // Botões
    if (captureBtn) captureBtn.style.display = 'none';
    if (refazerBtn) refazerBtn.style.display = 'inline-block';
    if (confirmarBtn) confirmarBtn.style.display = 'inline-block';

    console.log('✅ Preview exibido');
  }

  // ================== REFAZER ==================
  if (refazerBtn) {
    refazerBtn.addEventListener('click', function() {
      console.log('\n🔄 REFAZENDO - Voltando para câmera');

      imagemCapturada = null;
      esconderAnaliseModal(); // NOVO: garante overlay fechado
      
      if (captureBtn) captureBtn.style.display = 'inline-block';
      if (refazerBtn) refazerBtn.style.display = 'none';
      if (confirmarBtn) confirmarBtn.style.display = 'none';

      inicializarCamera();
    });
  }

  // ================== CONFIRMAR ==================
  if (confirmarBtn) {
    confirmarBtn.addEventListener('click', function() {
      console.log('\n✅ CONFIRMANDO SELFIE');
      console.log('📍 Enviando para /selfie/salvar/ com evento_id:', eventoId);

      if (!imagemCapturada) {
        alert('❌ Nenhuma imagem capturada');
        return;
      }

      // Desabilitar botão
      confirmarBtn.disabled = true;
      if (cameraStatus) cameraStatus.innerHTML = '⏳ Salvando imagem...';

      fetch('/selfie/salvar/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]')?.value || ''
        },
        body: JSON.stringify({
          image: imagemCapturada,
          evento_id: eventoId
        })
      })
      .then(response => {
        console.log('📥 Response recebido:', response.status);
        return response.json();
      })
      .then(data => {
        console.log('✅ Response JSON:', data);

        if (data.status === 'ok' || data.sucesso) {
          console.log('✅ SUCESSO ao salvar selfie');
          if (cameraStatus) cameraStatus.innerHTML = '✅ Selfie salva com sucesso! Redirecionando...';
          
          // Redirecionar
          setTimeout(() => {
            const redirectUrl = data.redirect_url || `/aluno/cadastro/?evento=${eventoId}`;
            console.log('🔗 Redirecionando para:', redirectUrl);
            window.location.href = redirectUrl;
          }, 1500);
        } else {
          console.error('❌ Erro ao salvar:', data.message || data.erro);
          alert('❌ ' + (data.message || data.erro || 'Erro ao salvar selfie'));
          confirmarBtn.disabled = false;
          if (cameraStatus) cameraStatus.innerHTML = '❌ Erro: ' + (data.message || data.erro);
        }
      })
      .catch(err => {
        console.error('❌ Erro na requisição:', err);
        alert('❌ Erro ao comunicar com servidor');
        confirmarBtn.disabled = false;
        if (cameraStatus) cameraStatus.innerHTML = '❌ Erro de conexão';
      });
    });
  }

  console.log('\n🎉 ========== SCRIPT CARREGADO COM SUCESSO ==========\n');
});
