# -*- coding: utf-8 -*-
"""Fluxo do formando - parte E: botao manual funcionar sempre (capturaManual)."""

T1 = (
    'botao manual: marca disparo manual',
    """    captureFallbackBtn.addEventListener('click', function() {
        if (countdownTimer || capturando) return;
        burstFeito = true;
        iniciarCountdown(2, 500);
    });""",
    """    captureFallbackBtn.addEventListener('click', function() {
        if (countdownTimer || capturando) return;
        burstFeito = true;
        capturaManual = true;   // PACOTE CALIBRAGEM SELFIE: disparo manual ignora o gate de rosto
        iniciarCountdown(2, 500);
    });""",
)

T2 = (
    'countdown nao cancela o disparo manual',
    """            if (!detectorUnavailable && !faceOk) {
                clearInterval(countdownTimer);""",
    """            if (!detectorUnavailable && !capturaManual && !faceOk) {
                clearInterval(countdownTimer);""",
)

T3 = (
    'disparo manual nao e barrado por faceOk',
    """        if (faceLandmarker && !faceOk) {
            burstFeito = false;""",
    """        if (faceLandmarker && !faceOk && !capturaManual) {   // PACOTE CALIBRAGEM SELFIE
            burstFeito = false;""",
)

T4 = (
    'disparo manual: volta ao modo automatico',
    """        capturando = true;
        pararGuias();   // congela a orientação durante o disparo (evita mensagens piscando)""",
    """        capturaManual = false;   // PACOTE CALIBRAGEM SELFIE: volta ao modo automatico
        capturando = true;
        pararGuias();   // congela a orientação durante o disparo (evita mensagens piscando)""",
)

T5 = (
    'tirar novamente: reseta modo manual',
    """    retakeBtn.addEventListener('click', function() {
        blobCapturado = null;""",
    """    retakeBtn.addEventListener('click', function() {
        capturaManual = false;   // PACOTE CALIBRAGEM SELFIE
        blobCapturado = null;""",
)

T6 = (
    'tentar novamente: reseta modo manual',
    """        // HOTFIX salvamento: destrava o overlay antes de reenquadrar (reversao: apagar estas 4 linhas)
        encerrarAnalise();
        tentativasReprovadas = 0;""",
    """        // HOTFIX salvamento: destrava o overlay antes de reenquadrar (reversao: apagar estas 4 linhas)
        encerrarAnalise();
        tentativasReprovadas = 0;
        capturaManual = false;   // PACOTE CALIBRAGEM SELFIE""",
)

TRANSFORMACOES = [T1, T2, T3, T4, T5, T6]
