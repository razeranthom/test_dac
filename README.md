# DAC - Teste de Back-end

## Instalação

### Python

### Pacotes

## Configuração

O arquivo .env contém a configuração do endpoint. Aqui está o default:

```
# URL sem a barra no final
URL = "http://localhost:8000"

ARQUIVO_TOKEN = "token_test.json"
ARQUIVO_CACHE = "cache_test.json"
```
No parâmetro URL, coloque o endpoint a ser testado, sem a barra final.

## Execução

Para executar os testes, no terminal rode o seguinte comando:

```
pytest -v test_dac.py
```
