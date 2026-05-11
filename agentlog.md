# Agent Log — Link Extractor Performance Test

Registro das atividades realizadas pelo agente de IA neste projeto.

---

## 2026-05-11 — Configuração e Execução Completa do Benchmarking

### Objetivo
Realizar benchmarking comparativo entre as implementações Python e Ruby da aplicação Link Extractor, com e sem cache Redis, variando o número de usuários virtuais.

### O que foi feito

#### 1. Configuração do Locust (`locust/locustfile.py`)
- Definida classe `LinkExtractorUser` com `wait_time = constant(0)` (sem espera entre requisições, carga máxima)
- Configuradas **10 URLs fixas** do Wikipedia que cada VU percorre em sequência por ciclo
- Endpoint: `GET /?url=<wikipedia_url>`, agrupado como `"Extract Links"` nas estatísticas

#### 2. Suporte a `ruby_nocache` (`api-ruby/`)
- Modificada a API Ruby (Sinatra) para respeitar a variável de ambiente `ENABLE_CACHE`
- Quando `ENABLE_CACHE=false`, o Redis é completamente ignorado — scraping real a cada requisição
- Isso foi necessário para criar o cenário `ruby_nocache` de forma simétrica ao `python_nocache`

#### 3. Script de automação (`scripts/run_tests.ps1`)
- Script PowerShell que itera sobre 4 cenários × 3 níveis de VUs = **12 testes**
- Para cada teste: sobe os serviços, limpa o Redis (`flushall`), executa o Locust headless, salva CSVs
- Ao final, chama os dois scripts Python para geração de gráficos
- Parâmetros: `-Duration` (padrão `1m`) e `-VUs` (padrão `@(1, 5, 10)`)

#### 4. Geração de gráficos (`scripts/generate-bar-graphs.py` e `generate-graphs.py`)
- **`generate-bar-graphs.py`**: gera 18 SVGs em `reports/bar_graphs/` — 6 métricas × 3 níveis de VU
  - Métricas: avg, p50, p90, p95, throughput, taxa de falha
  - Cores: Python cache (azul escuro), Python nocache (azul claro), Ruby cache (vermelho escuro), Ruby nocache (vermelho claro)
- **`generate-graphs.py`**: gera 4 SVGs de linha em `reports/graphs/` + `summary.csv`
  - Gráficos de linha: uma linha por cenário, eixo X = VUs (1, 5, 10)

#### 5. Execução dos testes
- Todos os 12 cenários executados com sucesso, duração de 1 minuto cada
- **0 falhas** em todos os cenários
- Total de requisições coletadas: de ~304 (python_nocache 1VU) a ~24.228 (ruby_nocache 10VUs)

### Resultados-chave

| Destaque | Valor |
|----------|-------|
| Maior throughput | Ruby nocache 10VU — **412 req/s** |
| Menor latência média | Ruby cache 1VU — **4.61 ms** |
| Pior latência | Python nocache — **~192–209 ms** (sem cache, scraping externo) |
| Ganho do cache para Python | ~34× de throughput (5.2 → 176 req/s com 1VU) |
| Taxa de falha em todos | **0%** |

### Arquivos gerados
- `reports/summary.csv` — tabela consolidada com todas as métricas
- `reports/bar_graphs/*.svg` — 18 gráficos de barras
- `reports/graphs/*.svg` — 4 gráficos de linha comparativos
- `reports/*_stats.csv` — CSVs individuais do Locust por cenário/VU (12 arquivos)
- `reports/*_stats_history.csv` — histórico temporal por cenário/VU (12 arquivos)
