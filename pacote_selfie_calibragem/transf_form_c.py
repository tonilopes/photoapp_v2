# -*- coding: utf-8 -*-
"""Fluxo do formando - parte C: loop de orientacao que nao morre."""

T1 = (
    'updateGuidance: wrapper anti-morte',
    """    function updateGuidance() {
        if (!guiasAtivas) return;          // parado durante captura/preview
        if (!faceLandmarker || video.readyState < 2) return;""",
    """    // ===== PACOTE CALIBRAGEM SELFIE (25/09/2026): este loop NUNCA pode morrer =====
    // CAUSA: sair daqui sem reagendar (video ainda sem quadro — camera frontal "fria" dos
    // Samsung — ou detector ausente) ou uma excecao do detectForVideo deixavam a tela
    // PARADA para sempre: sem auto-captura, sem aviso e com o botao manual escondido
    // (ele so aparecia se o DOWNLOAD do modelo falhasse) -> o aluno nao conseguia salvar.
    // REVERSAO: apagar o wrapper/agendarGuia e restaurar o corpo antigo da funcao.
    function updateGuidance() {
        try {
            updateGuidanceInterno();
        } catch (e) {
            guiaErros += 1;
            console.warn('updateGuidance erro #' + guiaErros + ':', e);
            if (guiaErros >= 3) {
                detectorUnavailable = true;
                captureFallbackBtn.classList.remove('d-none');
                setStatus('Verificação facial instável neste aparelho. Use o botão "Capturar Foto".', 'warning', false);
                return;
            }
            agendarGuia();
        }
    }

    // Reagenda o proximo quadro do loop (usado em TODAS as saidas da funcao).
    // NAO condicionar a guidanceFrame !== null: a primeira chamada (vinda do
    // loadFaceLandmarker) precisa INICIAR o loop. Com guiasAtivas=false (pararGuias) o
    // agendamento nao acontece e o epilogo zera guidanceFrame.
    function agendarGuia() {
        if (guiasAtivas && !detectorUnavailable) {
            guidanceFrame = requestAnimationFrame(updateGuidance);
        }
    }

    function updateGuidanceInterno() {
        if (!guiasAtivas) return;          // parado durante captura/preview
        if (detectorUnavailable) return;   // sem detector: o botao manual assume
        if (!faceLandmarker || !video.videoWidth || video.readyState < 2) { agendarGuia(); return; }""",
)

T2 = (
    'updateGuidance: epilogo',
    """        if (guiasAtivas) {
            guidanceFrame = requestAnimationFrame(updateGuidance);
        } else {
            guidanceFrame = null;
        }""",
    """        agendarGuia();
        if (!guiasAtivas) guidanceFrame = null;""",
)

T3 = (
    'updateGuidance: saida do alerta de expressao',
    """                    inicioQualidadeOk = null;
                    if (guidanceFrame !== null) guidanceFrame = requestAnimationFrame(updateGuidance);
                    return;""",
    """                    inicioQualidadeOk = null;
                    agendarGuia();
                    return;""",
)

TRANSFORMACOES = [T1, T2, T3]
