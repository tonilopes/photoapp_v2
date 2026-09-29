# -*- coding: utf-8 -*-
"""Modal publico - parte G: captura com camera pronta e recorte proporcional (cover)."""

T10 = (
    'captura: video pronto + recorte cover',
    """      // Canvas para captura
      const canvas = document.createElement('canvas');
      canvas.width = CONFIG_SELFIE.width;
      canvas.height = CONFIG_SELFIE.height;

      const ctx = canvas.getContext('2d');
      // Mirror
      ctx.scale(-1, 1);
      ctx.drawImage(video, -CONFIG_SELFIE.width, 0, CONFIG_SELFIE.width, CONFIG_SELFIE.height);""",
    """      // PACOTE CALIBRAGEM SELFIE: a camera frontal "fria" (comum nos Samsung) pode ainda
      // nao ter quadro — antes isso gerava foto preta ou esticada.
      // REVERSAO: apagar a verificacao e voltar ao drawImage esticado.
      if (!video.videoWidth || !video.videoHeight) {
        esconderAnaliseModal();
        retomarDeteccaoFacial();
        reabilitarBotaoCapturar();
        atualizarStatus('A câmera ainda está iniciando. Aguarde 1 segundo e toque em Capturar novamente.');
        return;
      }

      // Canvas para captura
      const canvas = document.createElement('canvas');
      canvas.width = CONFIG_SELFIE.width;
      canvas.height = CONFIG_SELFIE.height;

      // Recorte central (equivalente a object-fit: cover) em vez de esticar o quadro
      // 16:9 dentro de 3:4: mantem a proporcao do rosto (antes ele saia achatado).
      const ctx = canvas.getContext('2d');
      const escalaCapa = Math.max(CONFIG_SELFIE.width / video.videoWidth, CONFIG_SELFIE.height / video.videoHeight);
      const larguraCapa = video.videoWidth * escalaCapa;
      const alturaCapa = video.videoHeight * escalaCapa;
      ctx.save();
      ctx.translate(CONFIG_SELFIE.width, 0);
      ctx.scale(-1, 1);   // espelha igual ao preview
      ctx.drawImage(video, (CONFIG_SELFIE.width - larguraCapa) / 2, (CONFIG_SELFIE.height - alturaCapa) / 2, larguraCapa, alturaCapa);
      ctx.restore();""",
)

TRANSFORMACOES = [T10]
