#!/usr/bin/env bash
#
# Restaura os arquivos originais a partir do backup .bak_pacote_* mais recente.
# Uso (da raiz do projeto):  bash pacote_selfie_calibragem/reverter_pacote.sh
#
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

for DESTINO in \
  "$RAIZ/gestcaptur/static/gestcaptur/js/captura_selfie_modal.js" \
  "$RAIZ/templates/gestcaptur/formando_selfie_cadastro.html"
do
  PASTA="$(dirname "$DESTINO")"
  ULTIMO="$(ls -1 "$PASTA"/"$(basename "$DESTINO")".bak_pacote_* 2>/dev/null | sort | tail -n 1 || true)"
  if [ -z "${ULTIMO}" ]; then
    echo "AVISO: nenhum backup encontrado para $DESTINO"
    continue
  fi
  cp -v "$ULTIMO" "$DESTINO"
done

echo ""
echo "OK: revertido. Publique de novo:"
echo "  source venv/bin/activate && python manage.py collectstatic --noinput"
echo "  sudo /usr/local/bin/reiniciar-fotoid.sh"
