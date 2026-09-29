# Restaura os arquivos originais a partir do backup .bak_pacote_* mais recente.
#
# Uso (na raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File pacote_selfie_calibragem\reverter_pacote.ps1
#
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot

$destinos = @(
    (Join-Path $raiz 'gestcaptur\static\gestcaptur\js\captura_selfie_modal.js'),
    (Join-Path $raiz 'templates\gestcaptur\formando_selfie_cadastro.html')
)

foreach ($destino in $destinos) {
    $pasta = Split-Path -Parent $destino
    $nome = Split-Path -Leaf $destino
    $ultimo = Get-ChildItem -Path $pasta -Filter "$nome.bak_pacote_*" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime | Select-Object -Last 1
    if (-not $ultimo) {
        Write-Host "AVISO: nenhum backup encontrado para $destino"
        continue
    }
    Copy-Item $ultimo.FullName $destino -Force
    Write-Host "OK: $destino restaurado de $($ultimo.Name)"
}

Write-Host ""
Write-Host "Publique de novo:"
Write-Host "  python manage.py collectstatic --noinput"
Write-Host "  sudo /usr/local/bin/reiniciar-fotoid.sh"
