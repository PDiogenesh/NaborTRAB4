# Link Extractor Performance Test

Este projeto realiza testes de desempenho na aplicação Link Extractor, utilizando duas versões da API de extração (Python e Ruby) e o cache do Redis.

## Estrutura

- `api-python`: Serviço de extração desenvolvido em Python com Flask e Redis.
- `api-ruby`: Serviço de extração desenvolvido em Ruby com Sinatra e Redis.
- `www`: Front-end web desenvolvido em PHP.
- `locust`: Scripts do Locust para teste de carga.
- `reports`: Resultados (CSV) dos testes.
- `scripts`: Contém o script `run_tests.ps1` que automatiza a execução de cenários.
- `docker-compose.yaml`: Arquivo que orquestra a aplicação e o container do Locust.

## Execução

O script de automação no Windows permite rodar todos os cenários (Python/Ruby, com/sem cache, 1/5/10 usuários virtuais):

```powershell
./scripts/run_tests.ps1
```
