// gestcaptur/static/gestcaptur/js/captura_selfie_modal.js
// Captura de selfie pública em modal (similar ao fotografo)

document.addEventListener('DOMContentLoaded', function() {
  console.log('\n🚀 ========== INICIANDO CAPTURA_SELFIE_MODAL ==========');
  console.log('📱 Script captura_selfie_modal.js carregado');
  console.log('🔍 Verificando elementos DOM...');

  // Configurações
  const CONFIG_SELFIE = {
    width: 600,
    height: 800,
    quality: 0.85,
    maxSizeKB: 700
  };

  let imagemCapturada = null;
  let streamAtivo = null;
  let eventoId = null;
  let alunoId = null;
  let faceDetector = null;
  let faceDetectionFrame = null;
  let faceGuidance = { available: false, valid: false };
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
      faceDetector = await vision.FaceDetector.createFromOptions(fileset, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
        },
        runningMode: 'VIDEO',
        minDetectionConfidence: 0.65
      });
      faceGuidance.available = true;
      orientarEnquadramento(video);
    } catch (error) {
      console.warn('Orientação facial indisponível:', error);
      faceGuidance.available = false;
      atualizarStatus('Câmera pronta. Centralize seu rosto e mantenha boa iluminação.', false);
    }
  }

  function atualizarStatus(mensagem, falar = true) {
    if (cameraStatus) cameraStatus.textContent = mensagem;
    if (falar) falarAviso(mensagem.replace(/[📷✅⚠️❌]/g, '').trim());
  }

  function orientarEnquadramento(video) {
    if (!faceDetector || video.readyState < 2) return;
    const resultado = faceDetector.detectForVideo(video, performance.now());
    const faces = resultado.detections || [];
    faceGuidance.valid = false;

    if (faces.length === 0) {
      atualizarStatus('Aproxime o rosto e olhe para a câmera.');
    } else if (faces.length > 1) {
      atualizarStatus('Deixe apenas uma pessoa na frente da câmera.');
    } else {
      const box = faces[0].boundingBox;
      const centerX = box.originX + box.width / 2;
      const centerY = box.originY + box.height / 2;
      const centered = Math.abs(centerX - video.videoWidth / 2) < video.videoWidth * 0.18 &&
        Math.abs(centerY - video.videoHeight / 2) < video.videoHeight * 0.22;
      const goodSize = box.width > video.videoWidth * 0.22 && box.width < video.videoWidth * 0.82;

      if (!centered) {
        atualizarStatus('Centralize o rosto no oval da tela.');
      } else if (!goodSize) {
        atualizarStatus(box.width < video.videoWidth * 0.22 ? 'Aproxime um pouco o rosto.' : 'Afaste um pouco o rosto.');
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
    faceDetectionFrame = requestAnimationFrame(() => orientarEnquadramento(video));
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
      pararCamera();
    });
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
    console.log('\n[1/6] 🔍 Verificando suporte a getUserMedia...');
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.error('❌ getUserMedia NÃO DISPONÍVEL - Browser não suporta');
      if (cameraStatus) cameraStatus.innerHTML = '❌ Navegador não suporta câmera';
      alert('Seu navegador não suporta acesso à câmera. Use Chrome, Firefox ou Safari.');
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
          cameraStatus.innerHTML = mensagem;
          cameraStatus.style.color = '#ff6b6b';
        }
        alert(mensagem);

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
    captureBtn.addEventListener('click', function() {
      console.log('\n📸 CAPTURANDO FOTO');
      
      const video = document.getElementById('selfie-video');
      if (!video || !streamAtivo) {
        alert('❌ Câmera não está disponível');
        console.error('❌ Video não encontrado ou stream inativo');
        return;
      }

      if (faceGuidance.available && !faceGuidance.valid) {
        atualizarStatus('Ajuste o rosto no enquadramento antes de capturar.');
        return;
      }

      console.log('✅ Video element encontrado');

      // Canvas para captura
      const canvas = document.createElement('canvas');
      canvas.width = CONFIG_SELFIE.width;
      canvas.height = CONFIG_SELFIE.height;

      const ctx = canvas.getContext('2d');
      // Mirror
      ctx.scale(-1, 1);
      ctx.drawImage(video, -CONFIG_SELFIE.width, 0, CONFIG_SELFIE.width, CONFIG_SELFIE.height);

      imagemCapturada = canvas.toDataURL('image/jpeg', CONFIG_SELFIE.quality);
      console.log('✅ Imagem capturada');
      console.log('📊 Tamanho:', imagemCapturada.length, 'bytes');

      // Mostrar preview
      mostrarTelaPreview();
    });
  }

  // ================== PREVIEW ==================
  function mostrarTelaPreview() {
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
    img.style.transform = 'scaleX(-1)';

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
