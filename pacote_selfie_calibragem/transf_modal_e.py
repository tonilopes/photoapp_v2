# -*- coding: utf-8 -*-
"""Modal publico - parte E: mensagens de distancia corrigidas (invertidas antes)."""

T8B = (
    'mensagens de distancia corrigidas',
    """    if (faces.length === 0) {
      atualizarStatus('Aproxime o rosto e olhe para a câmera.');
    } else if (faces.length > 1) {
      atualizarStatus('Deixe apenas uma pessoa na frente da câmera.');
    } else {
      const box = faces[0].boundingBox;
      const centerX = box.originX + box.width / 2;
      const centerY = box.originY + box.height / 2;
      const centered = Math.abs(centerX - video.videoWidth / 2) < video.videoWidth * 0.15 &&
        Math.abs(centerY - video.videoHeight / 2) < video.videoHeight * 0.18;
      // Oval MENOR: exige rosto mais longe (~50-60cm) para caber, evitando
      // distorção grande-angular. Qualidade mantida (captura em alta resolução).
      const FACE_MIN = 0.28, FACE_MAX = 0.55;
      const goodSize = box.width > video.videoWidth * FACE_MIN && box.width < video.videoWidth * FACE_MAX;

      if (!centered) {
        atualizarStatus('Centralize o rosto no oval menor da tela.');
      } else if (!goodSize) {
        atualizarStatus(box.width < video.videoWidth * FACE_MIN ? 'Afaste o rosto até caber todo dentro do oval.' : 'Muito perto! Afaste bem o rosto até caber no oval.');
      } else {""",
    """    if (faces.length === 0) {
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
      } else {""",
)

TRANSFORMACOES = [T8B]
