param(
    [string]$Duration = "1m",
    [int[]]$VUs = @(1, 5, 10)
)

$ErrorActionPreference = "Stop"

# Vai para a raiz do projeto (pai de scripts/)
$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

$scenarios = @(
    @{key="python_cache";   api_host="api-python"; api_port="5000"; cache="true"},
    @{key="python_nocache"; api_host="api-python"; api_port="5000"; cache="false"},
    @{key="ruby_cache";     api_host="api-ruby";   api_port="4567"; cache="true"},
    @{key="ruby_nocache";   api_host="api-ruby";   api_port="4567"; cache="false"}
)

New-Item -ItemType Directory -Force -Path "reports" | Out-Null

Write-Host ""
Write-Host "=== Link Extractor - Testes de Desempenho ===" -ForegroundColor Cyan
Write-Host "Duracao por teste: $Duration | VUs: $($VUs -join ', ')"
Write-Host ""

foreach ($scenario in $scenarios) {
    Write-Host "=== Cenario: $($scenario.key) ===" -ForegroundColor Yellow

    # Configura variaveis de ambiente para o docker-compose
    $env:API_HOST    = $scenario.api_host
    $env:API_PORT    = $scenario.api_port
    $env:ENABLE_CACHE = $scenario.cache

    Write-Host "  Subindo servicos (API=$($scenario.api_host), Cache=$($scenario.cache))..."
    docker-compose up -d --force-recreate redis api-python api-ruby frontend
    Start-Sleep -Seconds 12

    foreach ($vu in $VUs) {
        Write-Host ""
        Write-Host "  -> $($scenario.key) | $vu VU(s) | $Duration" -ForegroundColor White

        # Limpa o Redis antes de cada teste (garante ponto de partida igual)
        Write-Host "     Limpando cache Redis..."
        docker-compose exec -T redis redis-cli flushall | Out-Null

        $prefix = "reports/$($scenario.key)_${vu}vu"

        docker-compose run --rm locust `
            -f locustfile.py `
            --host http://frontend `
            --headless `
            -u $vu `
            -r $vu `
            -t $Duration `
            --csv $prefix `
            --csv-full-history

        Write-Host "     Salvo: $prefix" -ForegroundColor Green
    }
}

docker-compose down

Write-Host ""
Write-Host "=== Testes concluidos! Gerando graficos... ===" -ForegroundColor Cyan

python scripts\generate-bar-graphs.py
python scripts\generate-graphs.py

Write-Host ""
Write-Host "Pronto! Veja os resultados em:" -ForegroundColor Green
Write-Host "  reports\bar_graphs\   (graficos de barras por metrica)"
Write-Host "  reports\graphs\       (graficos de linha comparativos)"
Write-Host "  reports\summary.csv   (tabela resumo de todas as metricas)"
