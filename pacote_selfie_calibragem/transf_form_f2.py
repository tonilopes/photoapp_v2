# -*- coding: utf-8 -*-
"""Fluxo do formando - parte F2: camera nativa do celular (plano B) e botao manual."""

T1 = (
    'plano B + liberacao manual',
    """    function iniciarCountdown(ticks = 3, intervalo = 800) {""",
    """    // Plano B: usa a camera NATIVA do celular (input capture) e entrega o arquivo no MESMO
    // fluxo de analise/preview/salvar (o servidor recebe o multipart 'foto' de sempre).
    function oferecerCameraDoCelular(motivo) {
        setStatus(motivo + ' Toque em "Usar a câmera do celular".', 'danger', false);
        const jaExiste = document.getElementById('btnCameraCelular');
        if (jaExiste) { jaExiste.classList.remove('d-none'); return; }

        const entrada = document.createElement('input');
        entrada.type = 'file';
        entrada.id = 'entradaCameraCelular';
        entrada.accept = 'image/*';
        entrada.setAttribute('capture', 'user');
        entrada.style.display = 'none';
        entrada.addEventListener('change', function() {
            const arquivo = entrada.files && entrada.files[0];
            if (!arquivo) return;
            blobCapturado = arquivo;
            try { previewImg.src = URL.createObjectURL(arquivo); } catch (e) { console.warn(e); }
            if (typeof encerrarAnalise === 'function') encerrarAnalise();
            if (typeof pararGuias === 'function') pararGuias();
            video.style.display = 'none';
            preview.style.display = 'block';
            setStatus('Foto escolhida! Confira e toque em Confirmar e Continuar.', 'success', false);
        });
        document.body.appendChild(entrada);

        const botao = document.createElement('button');
        botao.type = 'button';
        botao.id = 'btnCameraCelular';
        botao.className = 'btn btn-warning mt-2';
        botao.innerHTML = '<i class="bi bi-phone"></i> Usar a câmera do celular';
        botao.addEventListener('click', function() { entrada.click(); });
        const alvo = (captureFallbackBtn && captureFallbackBtn.parentNode)
            ? captureFallbackBtn.parentNode
            : cameraModal.querySelector('.modal-body');
        alvo.appendChild(botao);
    }

    // Se a captura automatica nao liberar em 12s, mostra o botao manual: o aluno NUNCA fica
    // sem uma forma de capturar a selfie.
    function agendarLiberacaoManual() {
        if (temporizadorManual) { clearTimeout(temporizadorManual); temporizadorManual = null; }
        temporizadorManual = setTimeout(function() {
            temporizadorManual = null;
            if (!faceOk && !blobCapturado && preview.style.display === 'none') {
                captureFallbackBtn.classList.remove('d-none');
                setStatus('Se a captura automática não disparar, toque em "Capturar Foto".', 'info', false);
            }
        }, GUIA.gracaManualMs);
    }

    function iniciarCountdown(ticks = 3, intervalo = 800) {""",
)

TRANSFORMACOES = [T1]
