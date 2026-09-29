# -*- coding: utf-8 -*-
"""Modal publico - parte C: wrapper que impede o loop de orientacao de morrer."""

T8A = (
    'orientarEnquadramento: wrapper anti-morte',
    """  function orientarEnquadramento(video) {
    if (!faceDetector || video.readyState < 2) return;
    const resultado = faceDetector.detectForVideo(video, performance.now());
    const faces = resultado.detections || [];
    faceGuidance.valid = false;""",
    """  // ===== PACOTE CALIBRAGEM SELFIE (25/09/2026): o loop de orientacao NUNCA pode morrer =====
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
    faceGuidance.valid = false;""",
)

TRANSFORMACOES = [T8A]
