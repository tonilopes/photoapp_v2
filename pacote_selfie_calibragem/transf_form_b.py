# -*- coding: utf-8 -*-
"""Fluxo do formando - parte B: MediaPipe (GPU -> CPU) e aviso amigavel."""

T1 = (
    'landmarker GPU->CPU (formando)',
    """            // FaceLandmarker (478 pontos) permite validar a POSE do rosto (perfil vs frontal)
            faceLandmarker = await vision.FaceLandmarker.createFromOptions(fileset, {
                baseOptions: {
                    modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
                    delegate: 'GPU'
                },
                runningMode: 'VIDEO',
                numFaces: 2
            });
            updateGuidance();""",
    """            // FaceLandmarker (478 pontos) permite validar a POSE do rosto (perfil vs frontal)
            // PACOTE CALIBRAGEM SELFIE: o delegate GPU falha em varios Androids (Adreno/One UI)
            // e o erro derrubava o loop de orientacao (aluno preso sem capturar).
            // REVERSAO: chamar createFromOptions direto com delegate: 'GPU'.
            let ultimoErro = null;
            for (const delegado of ['GPU', 'CPU']) {
                try {
                    faceLandmarker = await vision.FaceLandmarker.createFromOptions(fileset, {
                        baseOptions: {
                            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
                            delegate: delegado
                        },
                        runningMode: 'VIDEO',
                        numFaces: 2,
                        minFaceDetectionConfidence: GUIA.confiancaDeteccao
                    });
                    console.log('Detector facial criado (delegate=' + delegado + ')');
                    break;
                } catch (erroDelegate) {
                    ultimoErro = erroDelegate;
                    console.warn('Detector facial com delegate ' + delegado + ' falhou:', erroDelegate);
                    faceLandmarker = null;
                }
            }
            if (!faceLandmarker) throw (ultimoErro || new Error('Detector facial indisponivel'));
            updateGuidance();""",
)

T2 = (
    'aviso de detector indisponivel',
    """            detectorUnavailable = true;
            captureFallbackBtn.classList.remove('d-none');
            setStatus('Não foi possível ativar a verificação facial. Use o botão "Capturar Foto".', 'danger', false);""",
    """            detectorUnavailable = true;
            captureFallbackBtn.classList.remove('d-none');
            setStatus('Não foi possível ativar a verificação facial neste aparelho/rede. Use o botão "Capturar Foto" — a selfie vale igual.', 'danger', false);""",
)

TRANSFORMACOES = [T1, T2]
