# DAC - Teste de Back-end

DAC - UFPR

Aqui está o passo a passo para execução dos testes do Back-end da disciplina de DAC.

Este código está licenciado como [GNU GPL v3](https://github.com/razeranthom/test_dac/blob/main/LICENSE).

## Download do Repositório

Para fazer o download dos fontes do repositório, execute o seguinte comando no terminal:

```
git clone https://github.com/razeranthom/test_dac.git
```
Confira se tudo foi baixado na sua pasta corrente.

## Instalação

### Python

Você precisa do Python para executar os testes. Neste link você encontra um tutorial de como instalar o Python na sua máquina, seja MAC, Windows ou Linux:

[Installing Python](https://realpython.com/installing-python/)

### Pacotes

Para instalar os pacotes necessários, execute o seguinte comando no terminal.

```
pip3 install -r requirements.txt
```

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
pytest -s -v test_dac.py
```

Ao executar você vai perceber a criação de 2 arquivos (cujos nomes estão no arquivo .env). Um contém o token de login e outro contém um cache com dados que são usados entre as chamadas dos testes.


