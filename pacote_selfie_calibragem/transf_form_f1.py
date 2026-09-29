# -*- coding: utf-8 -*-
"""Fluxo do formando - parte F1: getUserMedia com 3 tentativas e retry de camera ocupada."""

T1 = (
    'getUserMedia com fallback',
    """    cameraModal.addEventListener('shown.bs.modal', function() {
        navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'user',
                width:  { ideal: 1920 },   // pede alta resolução ao hardware
                height: { ideal: 1440 }
            },
            audio: false
        }).then(stream => {
            streamAtual = stream;   // guardado para ImageCapture.takePhoto()
            video.srcObject = stream;
            video.play();
            setStatus('Analise do rosto iniciando. Olhe para a câmera.', 'info', false);
            guiasAtivas = true;
            loadFaceLandmarker();
        }).catch(err => {
            alert('Erro ao acessar câmera: ' + err.message);
            console.error(err);
        });
    });""",
    """    cameraModal.addEventListener('shown.bs.modal', function() {
        iniciarCameraFormando();
    });

    // ===== PACOTE CALIBRAGEM SELFIE (25/09/2026) =====
    // CAUSA: antes havia UMA unica tentativa de getUserMedia e, no erro, apenas um alert()
    // tecnico em ingles ("Could not start video source" = NotReadableError, o erro mais comum
    // nos Galaxys). Agora: 3 combinacoes de constraints, nova tentativa apos a camera
    // liberar e, se nada funcionar, a camera NATIVA do celular no MESMO fluxo.
    // REVERSAO: apagar estas funcoes e voltar ao bloco unico de getUserMedia + alert.
    const COMBINACOES_CAMERA = [
        { video: { facingMode: 'user', width: { ideal: 1920 }, height: { ideal: 1440 } }, audio: false },
        { video: { facingMode: 'user' }, audio: false },
        { video: true, audio: false }
    ];
    let retryLeituraFeito = false;

    function iniciarCameraFormando() {
        retryLeituraFeito = false;
        tentarCamera(0);
    }

    function tentarCamera(i) {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            oferecerCameraDoCelular('Este navegador não libera a câmera (comum em links abertos dentro do WhatsApp/Instagram).');
            return;
        }
        if (i >= COMBINACOES_CAMERA.length) {
            oferecerCameraDoCelular('Não foi possível abrir a câmera neste aparelho.');
            return;
        }
        navigator.mediaDevices.getUserMedia(COMBINACOES_CAMERA[i]).then(function(stream) {
            streamAtual = stream;   // guardado para ImageCapture.takePhoto()
            video.srcObject = stream;
            const play = video.play();
            if (play && play.catch) { play.catch(function(e) { console.warn('video.play() falhou:', e); }); }
            setStatus('Analise do rosto iniciando. Olhe para a câmera.', 'info', false);
            guiasAtivas = true;
            guiaDeteccoes = 0;
            loadFaceLandmarker();
            agendarLiberacaoManual();
        }).catch(function(err) {
            const nome = (err && err.name) || '';
            console.error('getUserMedia tentativa ' + (i + 1) + ' falhou:', nome, err && err.message);
            // Camera ainda presa por outro app/aba (tipico da Samsung): espera e tenta de novo
            if (nome === 'NotReadableError' && !retryLeituraFeito) {
                retryLeituraFeito = true;
                setStatus('Liberando a câmera (feche outros apps que estão usando a câmera)...', 'warning', false);
                setTimeout(function() { tentarCamera(i); }, GUIA.retryLeituraMs);
                return;
            }
            if (i + 1 < COMBINACOES_CAMERA.length) { tentarCamera(i + 1); return; }
            let msg = 'Não foi possível acessar a câmera neste aparelho.';
            if (nome === 'NotAllowedError') msg = 'Permissão da câmera negada. Libere a câmera nas configurações do navegador.';
            else if (nome === 'NotReadableError') msg = 'A câmera está em uso por outro aplicativo. Feche-o e tente novamente.';
            else if (nome === 'NotFoundError') msg = 'Não encontrei uma câmera neste aparelho.';
            oferecerCameraDoCelular(msg);
        });
    }""",
)

TRANSFORMACOES = [T1]
