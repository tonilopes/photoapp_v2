# Copia os arquivos prontos do pacote de calibragem da selfie para os caminhos do app,
# fazendo backup .bak_pacote_<data-hora> antes (permite reverter).
#
# Uso (na raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File pacote_selfie_calibragem\aplicar_pacote.ps1
#
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$selo = Get-Date -Format 'yyyyMMdd_HHmmss'

$mapa = @(
    @{ Origem = Join-Path $PSScriptRoot 'arquivos\captura_selfie_modal.js';
       Destino = Join-Path $raiz 'gestcaptur\static\gestcaptur\js\captura_selfie_modal.js' },
    @{ Origem = Join-Path $PSScriptRoot 'arquivos\formando_selfie_cadastro.html';
       Destino = Join-Path $raiz 'templates\gestcaptur\formando_selfie_cadastro.html' }
)

foreach ($par in $mapa) {
    if (-not (Test-Path $par.Origem)) { throw "Pacote incompleto: falta $($par.Origem)" }
    $backup = "$($par.Destino).bak_pacote_$selo"
    Copy-Item $par.Destino $backup -Force
    Copy-Item $par.Origem $par.Destino -Force
    Write-Host "OK: $($par.Destino)"
    Write-Host "    backup: $backup"
}

Write-Host ""
Write-Host "Publique agora:"
Write-Host "  python manage.py collectstatic --noinput"
Write-Host "  sudo /usr/local/bin/reiniciar-fotoid.sh"
Write-Host "Reverter: powershell -File pacote_selfie_calibragem\reverter_pacote.ps1"
