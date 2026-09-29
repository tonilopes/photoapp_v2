# -*- coding: utf-8 -*-
"""Modal publico - parte B: MediaPipe com queda GPU -> CPU."""

T4 = (
    'landmarker GPU->CPU',
    """      const vision = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs');
      const { FaceLandmarker, FilesetResolver } = vision;
      const fileset = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
      faceLandmarkerNovo = await FaceLandmarker.createFromOptions(fileset, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
          delegate: 'GPU'
        },
        runningMode: 'VIDEO',
        numFaces: 2, // >1 = intruso (foto colada)
        minFaceDetectionConfidence: 0.3,
        minFacePresenceConfidence: 0.3
      });""",
    """      const vision = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs');
      const { FaceLandmarker, FilesetResolver } = vision;
      const fileset = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
      faceLandmarkerNovo = await criarComDelegateFallback(FaceLandmarker, fileset, {
        modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
      }, {
        runningMode: 'VIDEO',
        numFaces: 2, // >1 = intruso (foto colada)
        minFaceDetectionConfidence: 0.3,
        minFacePresenceConfidence: 0.3
      });""",
)

T5 = (
    'helper criarComDelegateFallback',
    """  async function carregarLandmarkerSePreciso() {""",
    """  // PACOTE CALIBRAGEM SELFIE (25/09/2026): o delegate 'GPU' do MediaPipe falha em varios
  // Androids (Adreno/One UI) e, antes, o erro derrubava o loop de orientacao (tela travada,
  // aluno sem conseguir capturar). Agora tenta GPU e cai automaticamente para CPU.
  // REVERSAO: chamar Classe.createFromOptions(fileset, opcoes) direto com delegate: 'GPU'.
  async function criarComDelegateFallback(Classe, fileset, base, opcoes) {
    let ultimoErro = null;
    for (const delegado of ['GPU', 'CPU']) {
      try {
        const instancia = await Classe.createFromOptions(fileset, Object.assign({}, opcoes, {
          baseOptions: Object.assign({}, base, { delegate: delegado })
        }));
        console.log('✅ Detector facial criado (delegate=' + delegado + ')');
        return instancia;
      } catch (e) {
        ultimoErro = e;
        console.warn('⚠️ Detector facial com delegate ' + delegado + ' falhou:', e);
      }
    }
    throw (ultimoErro || new Error('Nao foi possivel criar o detector facial'));
  }

  async function carregarLandmarkerSePreciso() {""",
)

T6 = (
    'FaceDetector GPU->CPU',
    """      faceDetector = await vision.FaceDetector.createFromOptions(fileset, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
        },
        runningMode: 'VIDEO',
        minDetectionConfidence: 0.65
      });
      faceGuidance.available = true;
      orientarEnquadramento(video);""",
    """      faceDetector = await criarComDelegateFallback(vision.FaceDetector, fileset, {
        modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
      }, {
        runningMode: 'VIDEO',
        minDetectionConfidence: GUIA.confiancaDeteccao
      });
      faceGuidance.available = true;
      faceGuidance.deteccoes = 0;
      faceGuidance.erros = 0;
      faceGuidance.inicio = performance.now();
      orientarEnquadramento(video);""",
)

T7 = (
    'FaceDetector indisponivel',
    """      console.warn('Orientação facial indisponível:', error);
      faceGuidance.available = false;
      atualizarStatus('Câmera pronta. Centralize seu rosto e mantenha boa iluminação.', false);""",
    """      console.warn('Orientação facial indisponível:', error);
      faceGuidance.available = false;
      faceGuidance.deteccoes = 0;   // PACOTE CALIBRAGEM SELFIE: sem detector, captura manual livre
      atualizarStatus('Câmera pronta. Toque em Capturar quando estiver enquadrado.', false);""",
)

TRANSFORMACOES = [T4, T5, T6, T7]
