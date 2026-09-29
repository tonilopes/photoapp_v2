# -*- coding: utf-8 -*-
"""Modal publico - parte J: retry de camera ocupada, aviso final e limpeza no fechamento."""

T16 = (
    'NotReadableError: espera e tenta 1x',
    """        // Se chegou aqui, falhou de verdade
        console.error('\\n❌❌❌ getUserMedia ERRO CRÍTICO ❌❌❌');""",
    """        // PACOTE CALIBRAGEM SELFIE: NotReadableError ("Could not start video source") e o
        // erro mais comum nos Galaxys — a camera ainda esta presa por outro app/aba e libera
        // em menos de 1 segundo. Antes o aluno caia direto no erro.
        // REVERSAO: apagar este bloco.
        if (err.name === 'NotReadableError' && !retryLeituraFeito) {
          retryLeituraFeito = true;
          console.warn('⚠️  Câmera ocupada — aguardando liberação e tentando novamente...');
          if (cameraStatus) cameraStatus.innerHTML = '⏳ Liberando a câmera (feche outros apps que usam a câmera)...';
          setTimeout(function() { tentarGetUserMedia(1); }, GUIA.retryLeituraMs);
          return;
        }

        // Se chegou aqui, falhou de verdade
        console.error('\\n❌❌❌ getUserMedia ERRO CRÍTICO ❌❌❌');""",
)

T17 = (
    'erro final -> plano B',
    """        console.error('Mensagem para usuário:', mensagem);
        if (cameraStatus) {
          cameraStatus.innerHTML = mensagem;
          cameraStatus.style.color = '#ff6b6b';
        }
        alert(mensagem);""",
    """        console.error('Mensagem para usuário:', mensagem);
        if (cameraStatus) {
          cameraStatus.innerHTML = mensagem + ' Use o botão "Usar a câmera do celular".';
          cameraStatus.style.color = '#ff6b6b';
        }
        alert(mensagem + '\\n\\nDá para tirar a selfie com a câmera do próprio celular: toque em "Usar a câmera do celular".');
        oferecerCapturaPorArquivo(mensagem);""",
)

T18 = (
    'fechar modal: encerra o loop',
    """      if (typeof esconderAnaliseModal === 'function') esconderAnaliseModal();
      tentativasReprovadasModal = 0;
      pararCamera();""",
    """      if (typeof esconderAnaliseModal === 'function') esconderAnaliseModal();
      tentativasReprovadasModal = 0;
      pararDeteccaoFacial();   // PACOTE CALIBRAGEM SELFIE: encerra o loop de orientacao ao fechar
      pararCamera();""",
)

TRANSFORMACOES = [T16, T17, T18]
