param(
    [string]$Duration = "1m",
    [int[]]$Users = @(152, 155, 159),
    [int[]]$Instances = @(1, 2, 3),
    [string[]]$Scenarios = @()
)

$ErrorActionPreference = "Stop"

# URL da imagem de 1 MB (caminho relativo dentro do WordPress)
$img1mb = "/wp-content/uploads/2026/05/AsterNovi-belgii-flower-1mb-1.jpg"

# Cenarios:
#   texto_300kb  -> GET /?p=5  (post so texto, ~300 KB)
#   texto_400kb  -> GET /?p=8  (post so texto, ~400 KB)
#   imagem_1mb   -> GET /?p=15 + GET da imagem (HTML + imagem ~1 MB)
#   hibrido_3pag -> GET /?p=5, GET /?p=8, GET /?p=15 + imagem (3 paginas em sequencia)
$scenarioDefinitions = @(
    @{
        Key         = "texto_300kb"
        Path        = "/?p=5"
        Description = "Post de texto de aproximadamente 300 KB"
    },
    @{
        Key         = "texto_400kb"
        Path        = "/?p=8"
        Description = "Post de texto de aproximadamente 400 KB"
    },
    @{
        Key         = "imagem_1mb"
        Path        = "/?p=15,$img1mb"
        Description = "Post com imagem de 1 MB (HTML + GET explicito da imagem)"
    },
    @{
        Key         = "hibrido_3pag"
        Path        = "/?p=5,/?p=8,/?p=15,$img1mb"
        Description = "Hibrido: GET 300 KB + GET 400 KB + GET 1 MB (HTML + imagem) em sequencia"
    }
)

if ($Scenarios.Count -gt 0) {
    $requestedScenarios = @(
        $Scenarios |
            ForEach-Object { $_ -split "," } |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    )
    $scenarioDefinitions = @($scenarioDefinitions | Where-Object { $requestedScenarios -contains $_.Key })

    if ($scenarioDefinitions.Count -eq 0) {
        throw "Nenhum cenario encontrado. Use: texto_300kb, texto_400kb, imagem_1mb, hibrido_3pag."
    }
}

function Get-NginxConfig([int]$InstanceCount) {
    if ($InstanceCount -eq 1) { return "./nginx-1.conf" }
    if ($InstanceCount -eq 2) { return "./nginx-2.conf" }
    return "./nginx.conf"
}

function Get-SpawnRate([int]$UserCount) {
    if ($UserCount -le 152) { return 15 }
    if ($UserCount -le 155) { return 15 }
    return 16
}

New-Item -ItemType Directory -Force -Path "reports" | Out-Null

docker-compose up -d mysql-db wordpress1 wordpress2 wordpress3 locust

foreach ($instanceCount in $Instances) {
    $env:NGINX_CONF = Get-NginxConfig $instanceCount
    Write-Host ""
    Write-Host "=== Recriando Nginx com $instanceCount instancia(s): $env:NGINX_CONF ==="
    docker-compose up -d --force-recreate nginx
    Start-Sleep -Seconds 15

    foreach ($scenario in $scenarioDefinitions) {
        foreach ($userCount in $Users) {
            $spawnRate = Get-SpawnRate $userCount
            $prefix = "reports/$($scenario.Key)_${instanceCount}wp_${userCount}users"

            Write-Host ""
            Write-Host "=== $($scenario.Description) | $instanceCount WP | $userCount usuarios | $Duration ==="
            docker-compose exec -e TARGET_PATHS="$($scenario.Path)" locust locust `
                -f locustfile.py `
                --host http://nginx `
                --headless `
                -u $userCount `
                -r $spawnRate `
                -t $Duration `
                --csv $prefix `
                --csv-full-history
        }
    }
}

python scripts/generate-graphs.py
python scripts/generate-bar-graphs.py

Write-Host ""
Write-Host "Testes finalizados. Graficos em reports/graphs e reports/bar_graphs."
