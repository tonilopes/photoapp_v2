# -*- coding: utf-8 -*-
"""Fluxo do formando - parte A: configuracao GUIA e flags de captura manual."""

T1 = (
    'GUIA/flags do formando',
    """    const captureFallbackBtn = document.getElementById('captureFallbackBtn');
    let faceLandmarker = null;""",
    """    const captureFallbackBtn = document.getElementById('captureFallbackBtn');

    // ===== PACOTE CALIBRAGEM SELFIE (25/09/2026) =====
    // CAUSA: em celulares de FOV largo (ex.: Galaxy S23 Ultra, frontal ~80 graus) o rosto
    // ocupa MENOS largura do quadro. Com FACE_MIN=0.28 o app mandava a mensagem INVERTIDA
    // ("Afaste o rosto" com o rosto pequeno/longe) e o aluno nunca saia do loop:
    // "rosto nao reconhecido", "muito perto" estando longe, sem nunca capturar.
    // REVERSAO: apagar este bloco e restaurar FACE_MIN 0.28 / FACE_MAX 0.55 + mensagens antigas.
    console.log('PACOTE CALIBRAGEM SELFIE ativo (25/09/2026) - formando');
    const GUIA = {
        faceMin: 0.16,            // antes 0.28 — faixa realista para camera frontal larga
        faceMax: 0.50,            // antes 0.55
        confiancaDeteccao: 0.35,  // antes 0.5 (default) — rosto mais afastado e detectado
        gracaManualMs: 12000,     // apos 12s sem enquadramento, mostra o botao manual
        retryLeituraMs: 800,      // NotReadableError (tipico Samsung): espera e tenta 1x
        toleranciaCentroX: 0.20,  // antes 0.15
        toleranciaCentroY: 0.22   // antes 0.18
    };
    let guiaDeteccoes = 0;        // quantas vezes o detector avaliou de verdade
    let guiaErros = 0;            // excecoes seguidas do detector
    let capturaManual = false;    // disparo pelo botao manual (ignora o gate de rosto)
    let temporizadorManual = null;

    let faceLandmarker = null;""",
)

TRANSFORMACOES = [T1]
