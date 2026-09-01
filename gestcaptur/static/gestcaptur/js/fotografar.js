// gestcaptur/static/gestcaptur/js/fotografar.js
document.addEventListener('DOMContentLoaded', function() {
  console.log('📸 Script fotografar.js inicializado. Configuração: 600x800 (3:4)');

  // Função para pegar o CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Variáveis globais
  window.ultimoAlunoId = null;
  window.ultimoEventoId = null;
  window.streamAtivo = null;
  window.imagemCapturada = null;

  // 📸 CONFIGURAÇÕES FIXAS 3:4 (RETRATO)
  const CONFIG_FOTO = {
    width: 600,          // Largura fixa
    height: 800,         // Altura fixa (proporção 3:4)
    quality: 0.85,       // Qualidade JPEG (0.0 a 1.0)
    maxSizeKB: 700       // Tamanho máximo em KB
  };

  const CONFIG_CAMERA = {
    video: {
      facingMode: { ideal: "environment" }, // Prioriza câmera traseira
      width: { ideal: 1080, min: 720 },
      height: { ideal: 1440, min: 960 }
    }
  };

  // Abrir câmera para fotografar
  document.querySelectorAll('.js-abrir-camera').forEach(function(btn) {
    btn.addEventListener('click', function() {
      console.log('🎯 Botão fotografar clicado');
      
      // Verifica se o botão está desabilitado pelo atributo 'disabled' ou classe 'disabled'
      if (btn.disabled || btn.classList.contains('disabled')) {
        alert('Este evento não está liberado para fotografar. Aguarde o coordenador iniciar o evento.');
        return;
      }

      const alunoId = btn.dataset.alunoId;
      const eventoId = btn.dataset.eventoId;
      const alunoNome = btn.dataset.alunoNome;

      console.log('📋 Dados capturados:', { alunoId, eventoId, alunoNome });

      if (!alunoId || !eventoId) {
        alert('Erro: Dados do aluno ou evento não encontrados. Recarregue a página.');
        return;
      }

      // Salvar dados globalmente
      window.ultimoAlunoId = alunoId;
      window.ultimoEventoId = eventoId;

      // Configurar modal
      document.getElementById('aluno-info').innerText = alunoNome;
      document.getElementById('cameraModalLabel').innerText = 'Fotografar Aluno';
      
      // Configurar modal para captura
      configurarModalCaptura();

      // Mostrar modal
      const cameraModal = new bootstrap.Modal(document.getElementById('cameraModal'));
      cameraModal.show();

      // Inicializar câmera após modal abrir
      setTimeout(() => {
        inicializarCamera();
      }, 500); // Pequeno atraso para o modal ser totalmente renderizado
    });
  });

  // 🔧 CONFIGURAR MODAL PARA CAPTURA
  function configurarModalCaptura() {
    const footer = document.getElementById('camera-modal-footer');
    footer.innerHTML = `
      <button type="button" class="btn btn-outline-secondary btn-lg" id="btn-cancelar" data-bs-dismiss="modal">
        <i class="bi bi-x-lg"></i> Cancelar
      </button>
      <button type="button" class="btn btn-primary btn-lg" id="btn-capturar">
        <i class="bi bi-camera-fill"></i> Capturar
      </button>
    `;

    // Adicionar evento do botão capturar
    document.getElementById('btn-capturar').addEventListener('click', capturarFoto);
  }

  // 🔧 CONFIGURAR MODAL APÓS CAPTURA
  function configurarModalAposCaptura() {
    const footer = document.getElementById('camera-modal-footer');
    footer.innerHTML = `
      <button type="button" class="btn btn-warning btn-lg" id="btn-refazer">
        <i class="bi bi-camera-fill"></i> Refazer
      </button>
      <button type="button" class="btn btn-success btn-lg" id="btn-salvar">
        <i class="bi bi-check-lg"></i> Salvar
      </button>
    `;

    // Adicionar eventos
    document.getElementById('btn-refazer').addEventListener('click', refazerFoto);
    document.getElementById('btn-salvar').addEventListener('click', salvarFoto);
  }

  // 📹 INICIALIZAR CÂMERA COM PROPORÇÃO 3:4
  function inicializarCamera() {
    console.log('📹 Inicializando câmera - proporção 3:4');
    
    const cameraArea = document.getElementById('camera-area');
    cameraArea.innerHTML = `
      <div class="camera-container">
        <video id="video" autoplay playsinline muted></video>
        <div class="camera-overlay">
          <div class="camera-frame-34">
            <div class="frame-guide">
              <div class="guide-text">📷 Posicione o rosto aqui</div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    const video = document.getElementById('video');
    
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia(CONFIG_CAMERA)
        .then(function(stream) {
          console.log('✅ Câmera ativada');
          window.streamAtivo = stream;
          video.srcObject = stream;
          
          video.addEventListener('loadedmetadata', function() {
            console.log(`📐 Resolução da câmera: ${video.videoWidth}x${video.videoHeight}`);
            ajustarVideoParaProporção34(video);
          });
          
          video.play();
        })
        .catch(function(error) {
          console.log('⚠️ Tentando câmera frontal como fallback:', error);
          navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user" } // Tenta câmera frontal
          }).then(function(stream) {
            console.log('✅ Câmera frontal ativada');
            window.streamAtivo = stream;
            video.srcObject = stream;
            
            video.addEventListener('loadedmetadata', function() {
              ajustarVideoParaProporção34(video);
            });
            
            video.play();
          }).catch(function(error) {
            console.error('❌ Erro ao acessar câmera (nenhuma câmera disponível ou permissão negada):', error);
            alert('Erro ao acessar a câmera. Verifique as permissões do navegador.');
            // Oculta o modal de câmera se houver erro crítico
            const cameraModalElement = document.getElementById('cameraModal');
            const cameraModal = bootstrap.Modal.getInstance(cameraModalElement);
            if (cameraModal) cameraModal.hide();
          });
        });
    } else {
      alert('Seu navegador não suporta acesso à câmera.');
      const cameraModalElement = document.getElementById('cameraModal');
      const cameraModal = bootstrap.Modal.getInstance(cameraModalElement);
      if (cameraModal) cameraModal.hide();
    }
  }

  // 🔧 AJUSTAR VÍDEO PARA PROPORÇÃO 3:4
  function ajustarVideoParaProporção34(video) {
    const container = video.parentElement;
    
    // Definir proporção 3:4 no container
    container.style.aspectRatio = '3/4';
    container.style.width = '100%';
    container.style.maxWidth = '300px'; // Limite o tamanho para não ficar gigante em telas grandes
    
    // Ajustar vídeo para preencher o container (crop centralizado)
    video.style.width = '100%';
    video.style.height = '100%';
    video.style.objectFit = 'cover';
    video.style.objectPosition = 'center center';
    
    console.log('✅ Vídeo ajustado para proporção 3:4');
  }

  // 📸 CAPTURAR FOTO EM PROPORÇÃO 3:4 FIXA
  function capturarFoto() {
    console.log(`�� Capturando foto ${CONFIG_FOTO.width}x${CONFIG_FOTO.height} (3:4)`);
    
    const video = document.getElementById('video');
    if (!video || !window.streamAtivo) {
      alert('Erro: Câmera não está ativa');
      return;
    }

    // Criar canvas com dimensões fixas 3:4
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = CONFIG_FOTO.width;   // 600px
    canvas.height = CONFIG_FOTO.height; // 800px
    
    // Calcular área de crop do vídeo para manter proporção 3:4
    const videoWidth = video.videoWidth;
    const videoHeight = video.videoHeight;
    const videoAspect = videoWidth / videoHeight;
    const targetAspect = CONFIG_FOTO.width / CONFIG_FOTO.height; // 3:4 = 0.75
    
    let sourceX = 0, sourceY = 0, sourceWidth = videoWidth, sourceHeight = videoHeight;
    
    if (videoAspect > targetAspect) {
      // Vídeo mais largo - crop horizontal (centralizado)
      sourceWidth = videoHeight * targetAspect;
      sourceX = (videoWidth - sourceWidth) / 2;
    } else {
      // Vídeo mais alto - crop vertical (centralizado)
      sourceHeight = videoWidth / targetAspect;
      sourceY = (videoHeight - sourceHeight) / 2;
    }
    
    console.log(`🎯 Crop area: ${sourceX}, ${sourceY}, ${sourceWidth}x${sourceHeight}`);
    
    // Desenhar área cropada no canvas
    ctx.drawImage(
      video,
      sourceX, sourceY, sourceWidth, sourceHeight,  // Área do vídeo
      0, 0, CONFIG_FOTO.width, CONFIG_FOTO.height   // Canvas completo
    );

    // Comprimir imagem
    comprimirImagem(canvas, function(imagemComprimida) {
      window.imagemCapturada = imagemComprimida;
      
      // Mostrar preview da foto capturada
      document.getElementById('camera-area').innerHTML = `
        <div class="foto-preview">
          <div class="preview-container">
            <img src="${imagemComprimida}" alt="Foto capturada" />
            <div class="preview-info">
              <small>📸 ${CONFIG_FOTO.width}x${CONFIG_FOTO.height} • ${obterTamanhoImagem(imagemComprimida)} KB</small>
            </div>
          </div>
        </div>
      `;

      // Parar câmera
      pararCamera();

      // Configurar modal para pós-captura
      configurarModalAposCaptura();
      
      console.log(`✅ Foto capturada em ${CONFIG_FOTO.width}x${CONFIG_FOTO.height} pixels`);
    });
  }

  // 🗜️ COMPRIMIR IMAGEM PARA O TAMANHO MÁXIMO
  function comprimirImagem(canvas, callback) {
    let quality = CONFIG_FOTO.quality;
    let tentativas = 0;
    const maxTentativas = 10; // Aumentei o número máximo de tentativas
    const MIN_QUALITY = 0.4; // Qualidade mínima aceitável

    function tentar() {
      const dataURL = canvas.toDataURL('image/jpeg', quality);
      const tamanhoKB = obterTamanhoImagem(dataURL);
      
      console.log(`🗜️ Tentativa ${tentativas + 1}: ${tamanhoKB}KB (qualidade: ${Math.round(quality * 100)}%)`);
      
      if (tamanhoKB <= CONFIG_FOTO.maxSizeKB || tentativas >= maxTentativas || quality <= MIN_QUALITY) {
        callback(dataURL);
      } else {
        quality = Math.max(quality * 0.9, MIN_QUALITY); // Reduz a qualidade em 10%, mas não abaixo do mínimo
        tentativas++;
        // Usar setTimeout para evitar bloqueio da UI em caso de muitas tentativas (se fosse sincrono)
        // Como é recursivo e rápido, pode ser direto. Para grandes imagens, consideraria setTimeout(tentar, 0);
        tentar();
      }
    }

    tentar();
  }

  // 📏 OBTER TAMANHO DA IMAGEM EM KB
  function obterTamanhoImagem(dataURL) {
    const base64 = dataURL.split(',')[1];
    const bytes = atob(base64).length;
    return Math.round(bytes / 1024);
  }

  // 🔄 REFAZER FOTO
  function refazerFoto() {
    console.log('🔄 Refazendo foto');
    
    window.imagemCapturada = null;
    configurarModalCaptura(); // Volta para o estado inicial do modal
    
    setTimeout(() => {
      inicializarCamera(); // Reinicializa a câmera
    }, 300); // Pequeno atraso para re-renderização do modal
  }

  // 🛑 PARAR CÂMERA
  function pararCamera() {
    if (window.streamAtivo) {
      window.streamAtivo.getTracks().forEach(track => {
        track.stop();
        console.log('📹 Track da câmera parado:', track.kind);
      });
      window.streamAtivo = null;
    }
  }

  // 💾 SALVAR FOTO (Corrigido o ReferenceError)
  function salvarFoto() {
    console.log('💾 Salvando foto ' + CONFIG_FOTO.width + 'x' + CONFIG_FOTO.height);
    
    if (!window.imagemCapturada) {
      alert('Erro: Nenhuma foto capturada');
      return;
    }

    const alunoId = window.ultimoAlunoId;
    const eventoId = window.ultimoEventoId;

    if (!alunoId || !eventoId) {
      alert('Erro: Dados do aluno ou evento não encontrados. Recarregue a página.');
      return;
    }

    // --- CORREÇÃO DO ReferenceError: csrftoken DECLARADO ANTES DE SER USADO ---
    const csrftoken = getCookie('csrftoken'); // <-- AQUI DECLARAMOS E ATRIBUÍMOS csrftoken
    console.log('�� CSRF Token obtido:', csrftoken); // <-- ESTE CONSOLE.LOG AGORA DEVE APARECER!

    console.log('📤 Enviando foto ' + CONFIG_FOTO.width + 'x' + CONFIG_FOTO.height + ' para servidor');

    const btnSalvar = document.getElementById('btn-salvar');
    const btnRefazer = document.getElementById('btn-refazer');
    
    // Desabilita botões e mostra status de salvamento
    if (btnSalvar) {
        btnSalvar.disabled = true;
        btnSalvar.innerHTML = '<i class="bi bi-hourglass-split"></i> Salvando...';
    }
    if (btnRefazer) {
        btnRefazer.disabled = true;
    }

    const controller = new AbortController();
    // Timeout de 30 segundos para a requisição
    const timeoutId = setTimeout(() => controller.abort(), 30000); 

    fetch('/upload-foto/' + alunoId + '/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken // <-- AGORA USAMOS A VARIÁVEL 'csrftoken' CORRETAMENTE DECLARADA
      },
      body: JSON.stringify({
        image: window.imagemCapturada,
        evento_id: eventoId
      }),
      signal: controller.signal // Sinal para abortar a requisição em caso de timeout
    })
    .then(response => {
      clearTimeout(timeoutId); // Limpa o timeout se a requisição for concluída a tempo
      return response.json();
    })
    .then(data => {
      console.log('📨 Resposta do servidor:', data);
      
      if (data.status === 'ok') {
        // ✅ Atualizar a foto do aluno dinamicamente
        atualizarFotoDinamicamente(alunoId, data.foto_url);
        
        // Fechar o modal
        const cameraModalElement = document.getElementById('cameraModal');
        const cameraModal = bootstrap.Modal.getInstance(cameraModalElement);
        if (cameraModal) {
          cameraModal.hide();
        }
        
        alert('Foto salva com sucesso! ✅');
      } else {
        alert('Erro ao salvar: ' + (data.message || 'Erro desconhecido'));
        console.error('❌ Erro detalhado:', data);
      }
    })
    .catch(error => {
      clearTimeout(timeoutId); // Limpa o timeout em caso de erro também
      console.error('❌ Erro na requisição:', error);
      
      if (error.name === 'AbortError') {
        alert('Timeout: Envio demorou muito. Verifique sua conexão.');
      } else {
        alert('Erro de conexão. Verifique sua internet e tente novamente.');
      }
    })
    .finally(() => {
        // Reabilita botões após a conclusão da requisição
        if (btnSalvar) {
            btnSalvar.disabled = false;
            btnSalvar.innerHTML = '<i class="bi bi-check-lg"></i> Salvar';
        }
        if (btnRefazer) {
            btnRefazer.disabled = false;
        }
    });
  }

  // Limpar recursos quando modal fechar
  document.getElementById('cameraModal').addEventListener('hidden.bs.modal', function() {
    console.log('�� Modal fechado - limpando recursos');
    pararCamera();
    window.imagemCapturada = null;
    // Opcional: Limpar o conteúdo da camera-area para voltar ao estado inicial
    document.getElementById('camera-area').innerHTML = ''; 
  });
  // 📸 ATUALIZAR FOTO DINAMICAMENTE SEM RECARREGAR PÁGINA
  window.atualizarFotoDinamicamente = function(alunoId, fotoUrl) {
    console.log(`📸 Atualizando foto do aluno ${alunoId}:`, fotoUrl);
    
    // Encontrar o card do aluno
    const alunoCard = document.getElementById(`aluno-${alunoId}`);
    if (!alunoCard) {
      console.warn(`❌ Card do aluno ${alunoId} não encontrado. Recarregando página...`);
      location.reload();
      return;
    }

    // Encontrar o container do avatar
    const avatarContainer = alunoCard.querySelector('.col-auto');
    if (!avatarContainer) {
      console.warn('❌ Container de avatar não encontrado. Recarregando página...');
      location.reload();
      return;
    }

    // Buscar a foto URL do servidor com timestamp para evitar cache
    const fotoUrlComTimestamp = fotoUrl || `/media/fotos/?t=${Date.now()}`;
    
    // Limpar conteúdo anterior (ícone de pessoa-círculo)
    avatarContainer.innerHTML = '';

    // Criar nova imagem
    const img = document.createElement('img');
    img.src = fotoUrlComTimestamp;
    img.alt = `Foto do aluno ${alunoId}`;
    img.className = 'aluno-avatar com-foto';
    img.setAttribute('data-bs-toggle', 'modal');
    img.setAttribute('data-bs-target', `#fotoModal${alunoId}`);
    img.setAttribute('title', 'Clique para ampliar');
    
    // Adicionar evento de clique para atualizar o modal
    img.addEventListener('click', function(e) {
      e.preventDefault();
      const modalElement = document.getElementById(`fotoModal${alunoId}`);
      if (!modalElement) {
        console.warn(`❌ Modal #fotoModal${alunoId} não encontrado. Criando dinamicamente...`);
        criarModalFotoDinamicamente(alunoId, img.src);
      }
    });

    // Inserir imagem
    avatarContainer.appendChild(img);
    
    console.log(`✅ Foto do aluno ${alunoId} atualizada com sucesso!`);

    // Se o modal não existir, criar dinamicamente
    if (!document.getElementById(`fotoModal${alunoId}`)) {
      criarModalFotoDinamicamente(alunoId, img.src);
    }
  };

  // 🎬 CRIAR MODAL DE FOTO DINAMICAMENTE
  window.criarModalFotoDinamicamente = function(alunoId, fotoUrl) {
    const modalHtml = `
      <div class="modal fade" id="fotoModal${alunoId}" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h6 class="modal-title">Foto do Aluno</h6>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
              <img src="${fotoUrl}" alt="Foto" class="img-fluid" style="max-height: 500px; border-radius: 8px;">
            </div>
          </div>
        </div>
      </div>
    `;

    // Inserir modal no DOM
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer.firstElementChild);

    // Abrir o modal
    const modal = new bootstrap.Modal(document.getElementById(`fotoModal${alunoId}`));
    modal.show();
  };});