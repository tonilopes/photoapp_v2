# -*- coding: utf-8 -*-
"""Modal publico - parte H: preview com espelhamento opcional e avisos de navegador."""

T11 = (
    'mostrarTelaPreview com parametro',
    """  function mostrarTelaPreview() {""",
    """  function mostrarTelaPreview(espelhar) {
    pararDeteccaoFacial();   // PACOTE CALIBRAGEM SELFIE: nao deixa o loop de orientacao rodando no preview""",
)

T12 = (
    'preview: espelhar opcional',
    """    img.style.transform = 'scaleX(-1)';""",
    """    img.style.transform = (espelhar === false) ? 'none' : 'scaleX(-1)';""",
)

T14 = (
    'reset do retry de leitura',
    """  function continuarInicializacao() {
    console.log('\\n[1/6] 🔍 Verificando suporte a getUserMedia...');""",
    """  function continuarInicializacao() {
    retryLeituraFeito = false;   // PACOTE CALIBRAGEM SELFIE: cada abertura pode tentar de novo
    console.log('\\n[1/6] 🔍 Verificando suporte a getUserMedia...');""",
)

T15 = (
    'sem getUserMedia -> plano B',
    """      console.error('❌ getUserMedia NÃO DISPONÍVEL - Browser não suporta');
      if (cameraStatus) cameraStatus.innerHTML = '❌ Navegador não suporta câmera';
      alert('Seu navegador não suporta acesso à câmera. Use Chrome, Firefox ou Safari.');
      return;""",
    """      console.error('❌ getUserMedia NÃO DISPONÍVEL - Browser não suporta');
      if (cameraStatus) cameraStatus.innerHTML = '❌ Este navegador não libera a câmera (comum em links abertos dentro do WhatsApp/Instagram).';
      alert('Este navegador não libera a câmera — comum em links abertos dentro do WhatsApp ou Instagram.\\n\\nVamos usar a câmera do seu celular.');
      oferecerCapturaPorArquivo('Este navegador não libera a câmera.');
      return;""",
)

TRANSFORMACOES = [T11, T12, T14, T15]
