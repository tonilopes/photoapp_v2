# -*- coding: utf-8 -*-
"""Modal publico - parte A: configuracao GUIA, estado e retomada da deteccao."""

T1 = (
    'GUIA/config',
    """    quality: 0.9,   // antes 0.85
    maxSizeKB: 900
  };""",
    """    quality: 0.9,   // antes 0.85
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
  let retryLeituraFeito = false;""",
)

T2 = (
    'estado faceGuidance',
    """  let faceGuidance = { available: false, valid: false };""",
    """  // PACOTE CALIBRAGEM SELFIE: deteccoes/erros/inicio permitem saber se o detector
  // REALMENTE avaliou o rosto (o gate do botao "Capturar" so vale se deteccoes > 0) e
  // servem de cronometro para a liberacao manual. Reversao: voltar ao objeto antigo.
  let faceGuidance = { available: false, valid: false, deteccoes: 0, erros: 0, inicio: 0 };""",
)

T3 = (
    'retomarDeteccaoFacial',
    """      const v = document.getElementById('selfie-video');
      if (v && faceDetector && !faceDetectionFrame) {
        faceGuidance.available = true;
        faceDetectionFrame = requestAnimationFrame(function() { orientarEnquadramento(v); });
      }""",
    """      const v = document.getElementById('selfie-video');
      if (v && faceDetector && !faceDetectionFrame) {
        faceGuidance.available = true;
        faceGuidance.valid = false;
        faceGuidance.deteccoes = 0;   // PACOTE CALIBRAGEM SELFIE: so reabre o gate apos nova avaliacao
        faceGuidance.erros = 0;
        faceGuidance.inicio = performance.now();
        faceDetectionFrame = requestAnimationFrame(function() { orientarEnquadramento(v); });
      }""",
)

TRANSFORMACOES = [T1, T2, T3]
