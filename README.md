# Link Extractor — Teste de Desempenho

Projeto acadêmico de benchmarking comparativo entre implementações **Python** e **Ruby** da aplicação Link Extractor, com e sem cache Redis, sob diferentes cargas de usuários virtuais (VUs).

---

## Estrutura do Projeto

```
NaborTRAB4/
├── api-python/          # API em Python (Flask + Redis)
├── api-ruby/            # API em Ruby (Sinatra + Redis)
├── www/                 # Front-end em PHP
├── locust/
│   └── locustfile.py    # Script de carga: 10 URLs Wikipedia por VU
├── scripts/
│   ├── run_tests.ps1          # Automação completa dos testes (Windows)
│   ├── generate-bar-graphs.py # Gera gráficos de barras por métrica/VU
│   └── generate-graphs.py     # Gera gráficos de linha + summary.csv
├── reports/
│   ├── summary.csv            # Tabela consolidada de todas as métricas
│   ├── bar_graphs/            # 18 gráficos SVG de barras (6 métricas × 3 VUs)
│   └── graphs/                # 4 gráficos SVG de linha comparativos
└── docker-compose.yaml  # Orquestração dos serviços
```

---

## Cenários Testados

| Cenário          | API    | Cache Redis | VUs testados |
|------------------|--------|-------------|--------------|
| `python_cache`   | Python | ✅ Ativo    | 1, 5, 10     |
| `python_nocache` | Python | ❌ Inativo  | 1, 5, 10     |
| `ruby_cache`     | Ruby   | ✅ Ativo    | 1, 5, 10     |
| `ruby_nocache`   | Ruby   | ❌ Inativo  | 1, 5, 10     |

Cada usuário virtual executa **10 URLs do Wikipedia** em sequência, sem espera entre requisições, durante **1 minuto** por cenário.

---

## Como Executar

```powershell
# Executa todos os 12 cenários e gera os gráficos automaticamente
./scripts/run_tests.ps1

# Parâmetros opcionais:
./scripts/run_tests.ps1 -Duration "2m" -VUs @(1, 5, 10, 20)
```

O script realiza automaticamente:
1. Sobe os serviços via Docker Compose (`redis`, `api-python`, `api-ruby`, `frontend`)
2. Limpa o cache Redis antes de cada cenário
3. Executa o Locust headless e salva os CSVs em `reports/`
4. Ao final, gera todos os gráficos SVG e o `summary.csv`

---

## Resultados

### Tabela Resumo

| Cenário          | VUs | Avg (ms) | P50 (ms) | P90 (ms) | P95 (ms) | P99 (ms) | Req/s   | Falhas |
|------------------|-----|----------|----------|----------|----------|----------|---------|--------|
| python_cache     | 1   | 5.60     | 4        | 8        | 10       | 16       | 176.6   | 0%     |
| python_cache     | 5   | 19.07    | 16       | 27       | 35       | 61       | 260.0   | 0%     |
| python_cache     | 10  | 39.81    | 34       | 57       | 69       | 120      | 249.6   | 0%     |
| python_nocache   | 1   | 192.45   | 180      | 220      | 250      | 460      | 5.2     | 0%     |
| python_nocache   | 5   | 192.44   | 180      | 220      | 240      | 310      | 26.0    | 0%     |
| python_nocache   | 10  | 208.85   | 200      | 250      | 280      | 340      | 47.8    | 0%     |
| ruby_cache       | 1   | 4.61     | 4        | 7        | 8        | 14       | 214.0   | 0%     |
| ruby_cache       | 5   | 16.60    | 13       | 29       | 37       | 58       | 297.0   | 0%     |
| ruby_cache       | 10  | 36.24    | 31       | 59       | 72       | 100      | 270.6   | 0%     |
| ruby_nocache     | 1   | 4.67     | 4        | 7        | 9        | 15       | 210.9   | 0%     |
| ruby_nocache     | 5   | 13.61    | 12       | 20       | 23       | 35       | 362.9   | 0%     |
| ruby_nocache     | 10  | 23.87    | 22       | 33       | 40       | 61       | 412.3   | 0%     |

> Nenhum cenário apresentou falhas (0% failure rate).

---

### Principais Conclusões

- **Cache faz enorme diferença para Python**: sem cache, o Python satura em ~5 req/s (1 VU) por depender de scraping externo a cada requisição; com cache, atinge ~250 req/s.
- **Ruby sem cache superou todos**: o Ruby sem cache atingiu **412 req/s** com 10 VUs e latências mais baixas que os demais, sugerindo que sua implementação de scraping é mais eficiente.
- **Ruby com cache vs Python com cache**: Ruby ligeramente mais rápido em latência e throughput em todos os níveis de carga.
- **Escalabilidade**: todos os cenários com cache escalam bem até 5 VUs; acima disso, o throughput cresce menos que linearmente, indicando saturação do pool de conexões.

---

### Gráficos de Linha Comparativos

Os gráficos abaixo mostram a evolução das métricas conforme o número de VUs aumenta (1 → 5 → 10):

| Métrica | Arquivo |
|---------|---------|
| Tempo médio de resposta | `reports/graphs/comparacao_average_response_time.svg` |
| Mediana P50 | `reports/graphs/comparacao_50pct.svg` |
| P95 | `reports/graphs/comparacao_95pct.svg` |
| Throughput (req/s) | `reports/graphs/comparacao_requestsss.svg` |

### Gráficos de Barras por Nível de Carga

18 gráficos SVG gerados em `reports/bar_graphs/`, um por combinação de métrica e VU:

| Métrica              | 1 VU                          | 5 VUs                         | 10 VUs                         |
|----------------------|-------------------------------|-------------------------------|--------------------------------|
| Tempo médio (ms)     | `bar_graphs/avg_1vu.svg`      | `bar_graphs/avg_5vu.svg`      | `bar_graphs/avg_10vu.svg`      |
| P50 (ms)             | `bar_graphs/p50_1vu.svg`      | `bar_graphs/p50_5vu.svg`      | `bar_graphs/p50_10vu.svg`      |
| P90 (ms)             | `bar_graphs/p90_1vu.svg`      | `bar_graphs/p90_5vu.svg`      | `bar_graphs/p90_10vu.svg`      |
| P95 (ms)             | `bar_graphs/p95_1vu.svg`      | `bar_graphs/p95_5vu.svg`      | `bar_graphs/p95_10vu.svg`      |
| Throughput (req/s)   | `bar_graphs/throughput_1vu.svg` | `bar_graphs/throughput_5vu.svg` | `bar_graphs/throughput_10vu.svg` |
| Taxa de falha (%)    | `bar_graphs/taxa_falha_1vu.svg` | `bar_graphs/taxa_falha_5vu.svg` | `bar_graphs/taxa_falha_10vu.svg` |

---

## Dependências

- Docker + Docker Compose
- PowerShell 7+ (Windows)
- Python 3.x (para geração dos gráficos)
