# -*- coding: utf-8 -*-
"""Modal publico - parte F: remove o reagendamento antigo e destrava o gate do Capturar."""

T8C = (
    'remove reagendamento antigo',
    """    faceDetectionFrame = requestAnimationFrame(() => orientarEnquadramento(video));""",
    """    // PACOTE CALIBRAGEM SELFIE: o reagendamento do requestAnimationFrame passou a ser feito
    // pelo wrapper orientarEnquadramento() (bloco finally) — assim o loop nunca fica sem a
    // proxima volta, mesmo quando o video ainda esta aquecendo ou o detector falha.""",
)

T9 = (
    'gate do botao Capturar destravado',
    """      if (faceGuidance.available && !faceGuidance.valid) {
        atualizarStatus('Ajuste o rosto no enquadramento antes de capturar.');
        return;
      }""",
    """      // PACOTE CALIBRAGEM SELFIE: o gate so vale se o detector REALMENTE ja avaliou o rosto
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
      }""",
)

TRANSFORMACOES = [T8C, T9]
