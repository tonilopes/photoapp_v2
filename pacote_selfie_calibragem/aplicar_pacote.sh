#!/usr/bin/env bash
#
# Copia os arquivos do pacote de calibragem da selfie para os caminhos do app.
# Faz backup .bak_pacote_<data-hora> antes de sobrescrever (permite reverter).
#
# Uso (da raiz do projeto):  bash pacote_selfie_calibragem/aplicar_pacote.sh
#
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
SELO="$(date +%Y%m%d_%H%M%S)"
PACOTE="$RAIZ/pacote_selfie_calibragem/arquivos"

JS_DEST="$RAIZ/gestcaptur/static/gestcaptur/js/captura_selfie_modal.js"
TPL_DEST="$RAIZ/templates/gestcaptur/formando_selfie_cadastro.html"

for par in "$PACOTE/captura_selfie_modal.js|$JS_DEST" "$PACOTE/formando_selfie_cadastro.html|$TPL_DEST"; do
  ORIGEM="${par%%|*}"
  DESTINO="${par##*|}"
  if [ ! -f "$ORIGEM" ]; then
    echo "ERRO: pacote incompleto, falta $ORIGEM (rode aplicar_transformacoes.py primeiro)"
    exit 1
  fi
  cp -v "$DESTINO" "$DESTINO.bak_pacote_$SELO"
  cp -v "$ORIGEM" "$DESTINO"
done

echo ""
echo "OK: pacote aplicado (backups .bak_pacote_$SELO criados ao lado dos originais)."
echo "Publique agora:"
echo "  source venv/bin/activate && python manage.py collectstatic --noinput"
echo "  sudo /usr/local/bin/reiniciar-fotoid.sh"
echo "Para reverter: bash pacote_selfie_calibragem/reverter_pacote.sh"
