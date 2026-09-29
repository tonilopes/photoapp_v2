# -*- coding: utf-8 -*-
"""Fluxo do formando - parte D: faixa de distancia realista e mensagens corrigidas."""

T1 = (
    'conta avaliacoes do detector',
    """        const result = faceLandmarker.detectForVideo(video, performance.now());
        const faces = result.faceLandmarks || [];
        faceOk = false;""",
    """        const result = faceLandmarker.detectForVideo(video, performance.now());
        const faces = result.faceLandmarks || [];
        guiaDeteccoes += 1;   // PACOTE CALIBRAGEM SELFIE: conta avaliacoes reais do detector
        faceOk = false;""",
)

T2 = (
    'faixa de distancia realista',
    """            const centered = Math.abs(centerX - video.videoWidth / 2) < video.videoWidth * .15 &&
                Math.abs(centerY - video.videoHeight / 2) < video.videoHeight * .18;
            // FAIXA IDEAL MENOR: oval reduzido (~44% largura) -> rosto precisa ficar
            // mais LONGE (~50-60cm) para caber, evitando distorção grande-angular.
            // Mantém qualidade: captura continua em alta resolução (1920px).
            const FACE_MIN = 0.28, FACE_MAX = 0.55;""",
    """            // PACOTE CALIBRAGEM SELFIE: tolerancia de centralizacao um pouco maior
            // (antes .15/.18) — segurar o celular na mao nunca e perfeito.
            const centered = Math.abs(centerX - video.videoWidth / 2) < video.videoWidth * GUIA.toleranciaCentroX &&
                Math.abs(centerY - video.videoHeight / 2) < video.videoHeight * GUIA.toleranciaCentroY;
            // FAIXA IDEAL DE DISTANCIA: o rosto dentro do oval (~44% da largura) mede 40-50%
            // da largura; em camera de FOV largo (S23 Ultra) mede 16-35%. O piso 0.28 era
            // inalcancavel e gerava o loop "afaste/aproxime" sem nunca capturar.
            // REVERSAO: FACE_MIN 0.28, FACE_MAX 0.55.
            const FACE_MIN = GUIA.faceMin, FACE_MAX = GUIA.faceMax;""",
)

T3 = (
    'mensagens de distancia corrigidas',
    """            } else if (!correctSize) {
                setStatus(larguraRosto < video.videoWidth * FACE_MIN ? '↔️ Afaste o rosto: deixe-o menor, cabendo todo dentro do oval.' : '⚠️ Muito perto! Afaste bem o rosto até caber todo dentro do oval.', 'warning');
            } else if (dePerfil) {""",
    """            } else if (larguraRosto <= video.videoWidth * FACE_MIN) {
                // PACOTE CALIBRAGEM SELFIE: aqui a mensagem estava INVERTIDA (mandava
                // afastar quando o rosto estava longe/pequeno) — prendia o aluno no loop.
                setStatus('↔️ Aproxime o rosto: ele está pequeno demais para caber no oval.', 'warning');
            } else if (larguraRosto >= video.videoWidth * FACE_MAX) {
                setStatus('⚠️ Afaste um pouco o rosto: ele está maior que o oval.', 'warning');
            } else if (!correctSize) {
                setStatus('Ajuste a distância até o rosto caber no oval.', 'warning');
            } else if (dePerfil) {""",
)

TRANSFORMACOES = [T1, T2, T3]
