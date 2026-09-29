# -*- coding: utf-8 -*-
"""Fluxo do formando - parte G: limpeza ao fechar o modal e texto de apoio do oval."""

T1 = (
    'fechar modal: limpa estados novos',
    """        capturando = false;
        burstFeito = false;
        inicioQualidadeOk = null;
        btnTentarNovamente.classList.add('d-none');""",
    """        capturando = false;
        burstFeito = false;
        capturaManual = false;      // PACOTE CALIBRAGEM SELFIE
        guiaDeteccoes = 0;
        guiaErros = 0;
        if (temporizadorManual) { clearTimeout(temporizadorManual); temporizadorManual = null; }
        inicioQualidadeOk = null;
        btnTentarNovamente.classList.add('d-none');""",
)

T2 = (
    'texto de apoio do oval',
    """                <div class="face-guide-hint" aria-hidden="true">↔️ Afaste o rosto até caber no oval</div>""",
    """                <div class="face-guide-hint" aria-hidden="true">↔️ Ajuste a distância até o rosto caber no oval (sem cortar)</div>""",
)

TRANSFORMACOES = [T1, T2]
