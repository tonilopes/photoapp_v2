# gestcaptur/utils/imagens.py
"""
Pipeline de processamento de imagens de selfie (Fase 2).

Aplicado em todos os fluxos de selfie (pública, obrigatória e formandos):
- Correção de rotação EXIF (arquivos enviados por upload podem chegar deitados)
- Redimensionamento para no máximo 1200px no lado maior (Lanczos)
- Autocontraste suave (cutoff=1): corrige selfies lavadas/escuras sem exagero
- Re-encode JPEG otimizado (quality 90, progressive): arquivos ~30% menores
- Remove metadados (EXIF/GPS) da imagem final — privacidade do formando

Nunca amplia a imagem: se o original for menor que o limite, sai no tamanho original.
"""

import io
import logging

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

LADO_MAXIMO_PADRAO = 1200
JPEG_QUALITY_PADRAO = 90


def processar_selfie(image_bytes, lado_maximo=LADO_MAXIMO_PADRAO, qualidade=JPEG_QUALITY_PADRAO,
                     aplicar_autocontraste=True):
    """
    Normaliza e otimiza os bytes de uma selfie.

    Recebe bytes de imagem (JPEG/PNG/WebP) e devolve a tupla
    (jpeg_bytes, largura, altura) já processada.

    Erros de decodificação (UnidentifiedImageError/OSError) propagam para o
    chamador, que já possui tratamento próprio para arquivos inválidos.
    """
    imagem = Image.open(io.BytesIO(image_bytes))
    imagem = ImageOps.exif_transpose(imagem)  # corrige rotação EXIF
    imagem = imagem.convert('RGB')            # JPEG não suporta alpha/paleta

    if max(imagem.size) > lado_maximo:
        imagem.thumbnail((lado_maximo, lado_maximo), Image.LANCZOS)

    if aplicar_autocontraste:
        try:
            imagem = ImageOps.autocontrast(imagem, cutoff=1)
        except Exception:
            # Reforço de contraste é best-effort; nunca deve quebrar a captura
            logger.warning('Autocontraste falhou; salvando sem ajuste.', exc_info=True)

    buffer = io.BytesIO()
    imagem.save(buffer, format='JPEG', quality=qualidade, optimize=True, progressive=True)
    return buffer.getvalue(), imagem.width, imagem.height
