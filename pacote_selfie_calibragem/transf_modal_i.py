# -*- coding: utf-8 -*-
"""Modal publico - parte I: PLANO B (camera nativa do celular pelo input capture)."""

T13 = (
    'plano B: camara do celular',
    """  // ================== PARAR CÂMERA ==================
  function pararCamera() {""",
    """  // ===== PACOTE CALIBRAGEM SELFIE (25/09/2026): PLANO B universal =====
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
  function pararCamera() {""",
)

TRANSFORMACOES = [T13]
