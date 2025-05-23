######################################################
# Testador de Back-end da disciplina de DAC
#
# Autor: Prof. Dr. Razer Anthom Nizer Rojas Montaño
#
# Necessário PyTest para execução
######################################################
from dotenv import load_dotenv
import requests, os, time, json, datetime, random
from datetime import timedelta, datetime

### Biblioteca para simplificação de acesso a dados
from test_dados import *

### Header padrão sendo enviado nas comunicações
HEADERS = {
    'Accept': '*/*',
    'User-Agent': 'request'
}

### Carga dos parâmetros no arquivo .env
load_dotenv()
URL = os.getenv("URL")
ARQUIVO_TOKEN = os.getenv("ARQUIVO_TOKEN")
ARQUIVO_CACHE = os.getenv("ARQUIVO_CACHE")


####################################################
# Funções Helpers

def salvar_token(token):
    with open(ARQUIVO_TOKEN, "w") as fp:
        fp.write(token)

def recuperar_token():
    with open(ARQUIVO_TOKEN, "r") as fp:
        token = fp.readline()
    return token

def salvar_cache(cache):
    cache_s = json.dumps(cache)
    with open(ARQUIVO_CACHE, "w") as fp:
        fp.write(cache_s)

def recuperar_cache():
    if not os.path.exists(ARQUIVO_CACHE):
        return {}
    with open(ARQUIVO_CACHE, "r") as fp:
        cache = json.load(fp)
    return cache

def inserir_ou_alterar_cache(lista):
    cache = recuperar_cache()
    for l in lista:
        cache[l[0]] = l[1]

    salvar_cache(cache)

#### TODO Usar o Faker na próxima versão!!!
def gerar_cpf():                                                        
    cpf = [random.randint(0, 9) for x in range(9)]                              
                                                                               
    for _ in range(2):                                                          
        val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11                                                                                   
        cpf.append(11 - val if val > 1 else 0)                                  
                                                                                
    return '%s%s%s%s%s%s%s%s%s%s%s' % tuple(cpf)

def obter_novo_codigo(quantidade=4):
    numeros = "0123456789"
    generated_numero = ''.join(random.choices(numeros, k = quantidade))
    return generated_numero

def gerar_email():
    return f"func_{obter_novo_codigo(2)}@gmail.com"

def gerar_senha():
    return obter_novo_codigo(4)


####################################################
# Agora começam as funções de teste ao back-end
####################################################


####################################################
# R00 - Reboot - apagar base

def test_r00_reboot():

    resp = requests.get(URL + f"/reboot", 
                         headers=HEADERS)


####################################################
# R01 - Autocadastro

def test_r01_autocadastro():

    cpf = gerar_cpf()
    email = "razer@ufpr.br"
    USUARIO1["cpf"] = cpf
    USUARIO1["email"] = email
    USUARIO1["nome"] = "Usuário 1"
    resp = requests.post(URL + "/clientes", 
                         headers=HEADERS, 
                         json=USUARIO1)
    
    assert resp.status_code==201

    r = resp.json()
    assert r['cpf']==cpf
    assert r['email']==email

    print()
    senha = input(f"    >>>> Digite a senha enviada no e-mail {email}: ")

    inserir_ou_alterar_cache([ 
        ("cliente_codigo", r["codigo"]),
        ("cliente_cpf", r["cpf"]),
        ("cliente_email", r["email"]),
        ("cliente_senha", senha),
    ])


def test_r01_autocadastro_duplicado():

    cache = recuperar_cache()

    USUARIO1["cpf"] = cache["cliente_cpf"]
    USUARIO1["email"] = cache["cliente_email"]
    USUARIO1["nome"] = "Usuário 1"
    resp = requests.post(URL + "/clientes", 
                         headers=HEADERS, 
                         json=USUARIO1)
    
    assert resp.status_code==409

####################################################
# R02 - Login

def test_r02_acesso_endpoint_sem_logar():

    cache = recuperar_cache()
    cliente = cache["cliente_codigo"]

    resp = requests.get(URL + f"/clientes/{cliente}", 
                         headers=HEADERS)
    
    # ainda não está logado, não pode acessar
    assert resp.status_code==401

def test_r02_acesso_endpoint_token_incorreto():

    HEADERS["Authorization"] = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2dpbiI6ImZ1bmNfOTlAZ21haWwuY29tIiwic2VuaGEiOiI1NjQzIiwiZXhwIjoxNzQxODA5MzI4fQ.1mZHb2FFarMywbYdocvittD-SQdzNV7WvPeT5VRQ3h8"
    cache = recuperar_cache()
    cliente = cache["cliente_codigo"]

    resp = requests.get(URL + f"/clientes/{cliente}", 
                         headers=HEADERS)
    
    # ainda não está logado, não pode acessar
    assert resp.status_code==401




def test_r02_login_erro():
    LOGIN["login"] = gerar_email()
    LOGIN["senha"] = gerar_senha()
    resp = requests.post(URL + "/login", 
                         headers=HEADERS, 
                         json=LOGIN)
    
    assert resp.status_code==401

def test_r02_login_ok():
    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    email = cache["cliente_email"]
    cpf = cache["cliente_cpf"]
    senha = cache["cliente_senha"]

    LOGIN["login"] = email
    LOGIN["senha"] = senha

    resp = requests.post(URL + "/login", 
                         headers=HEADERS, 
                         json=LOGIN)
    
    assert resp.status_code==200 

    r = resp.json()
    assert "access_token" in r
    assert "token_type" in r
    assert r["usuario"]["codigo"] == codigo
    assert r["usuario"]["cpf"] == cpf
    assert r["usuario"]["email"] == email
    assert r["tipo"] == "CLIENTE"

    ACCESS_TOKEN = r["access_token"]

    # Adiciona o token retornado para as próximas chamadas
    salvar_token(f"Bearer {ACCESS_TOKEN}")


def test_r02_logout():

    token = recuperar_token()
    HEADERS["Authorization"] = token
    
    cache = recuperar_cache()
    email = cache["cliente_email"]

    LOGOUT = {
        "login" : email
    }
    resp = requests.post(URL + "/logout", 
                         headers=HEADERS, 
                         json=LOGOUT)
    
    assert resp.status_code==200

    salvar_token(f"")


####################################################
# Login para o testes com cliente

def test_r02_login_sistema():
    # Loga com o usuário recém criado, para usar o sistema
    test_r02_login_ok()

####################################################
# R03 - Mostrar Tela Inicial do Cliente

def test_r03_busca_todos_clientes():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    resp = requests.get(URL + f"/clientes", 
                         headers=HEADERS)

    assert resp.status_code==200

    r = resp.json()
    assert len(r)>0



def test_r03_dados_cliente():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    ### Busca um cliente inexistente
    codigo_errado = obter_novo_codigo()
    resp = requests.get(URL + f"/clientes/{codigo_errado}", 
                         headers=HEADERS)

    assert resp.status_code==404

    ### Busca o cliente recém cadastrado
    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    email = cache["cliente_email"]
    cpf = cache["cliente_cpf"]
    senha = cache["cliente_senha"]

    resp = requests.get(URL + f"/clientes/{codigo}", 
                         headers=HEADERS)

    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==codigo
    assert r["email"]==email
    assert r["cpf"]==cpf

# Precisa ser testado 2 vezes, uma no início sem reservas e depois com reservas
def test_r03_buscar_reservas_vazias():

    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]

    resp = requests.get(URL + f"/clientes/{codigo}/reservas", 
                         headers=HEADERS)

    # na primeira tentativa devem vir reservas vazias
    assert resp.status_code==204


####################################################
# R05 - Comprar Milhas

def test_r05_comprar_milhas1():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]

    milhas = random.randint(1000, 2000)
    json_milhas = {
        "quantidade": milhas
    }
    resp = requests.put(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS,
                         json=json_milhas)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==codigo and r["saldo_milhas"]==milhas

    inserir_ou_alterar_cache([ ("milhas1", milhas) ])
    
def test_r05_comprar_milhas2():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    milhas1 = int(cache["milhas1"])

    milhas = random.randint(100, 200)
    json_milhas = {
        "quantidade": milhas
    }
    resp = requests.put(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS,
                         json=json_milhas)
    
    r = resp.json()
    assert resp.status_code==200 
    assert r["codigo"]==codigo and r["saldo_milhas"]==(milhas1+milhas)

    inserir_ou_alterar_cache([ ("milhas2", milhas) ])

    
####################################################
# R06 - Extrato de Milhas

def test_r06_extrato_milhas():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    milhas1 = int(cache["milhas1"])
    milhas2 = int(cache["milhas2"])
    inserir_ou_alterar_cache([ ("saldo_milhas", (milhas1+milhas2)) ])

    resp = requests.get(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==codigo and r["saldo_milhas"]==(milhas1+milhas2)
    assert len(r["transacoes"]) == 2
    assert r["transacoes"][0]["quantidade_milhas"] == milhas1 and r["transacoes"][0]["tipo"] == "ENTRADA"
    assert r["transacoes"][1]["quantidade_milhas"] == milhas2 and r["transacoes"][0]["tipo"] == "ENTRADA"

####################################################
# R07 - Efetuar Reserva

def test_r07_buscar_voos():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    agora = datetime.now()
    data_voo_str = agora.strftime("%Y-%m-%dT%H:%M:%S-03:00")

    #### 1o voo
    params = {
        "data": data_voo_str,
        "origem": VOO1_PRE_ORIGEM,
        "destino": VOO1_PRE_DESTINO
    }
    resp = requests.get(URL + f"/voos", 
                         headers=HEADERS, params=params)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["origem"]==VOO1_PRE_ORIGEM and r["destino"]==VOO1_PRE_DESTINO
    assert len(r["voos"])>0

    data_dt = time.strptime(r["data"][:10], "%Y-%m-%d")
    for v in r["voos"]:
        assert v["aeroporto_origem"]["codigo"] == VOO1_PRE_ORIGEM
        assert v["aeroporto_destino"]["codigo"] == VOO1_PRE_DESTINO
        v_dt =  time.strptime(v["data"][:10], "%Y-%m-%d")
        assert v_dt > data_dt

    inserir_ou_alterar_cache( [ 
        ("voo1", r["voos"][0]["codigo"])
    ] )

    ###### 2o voo
    params = {
        "data": data_voo_str,
        "origem": VOO2_PRE_ORIGEM,
        "destino": VOO2_PRE_DESTINO
    }
    resp = requests.get(URL + f"/voos", 
                         headers=HEADERS, params=params)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["origem"]==VOO2_PRE_ORIGEM and r["destino"]==VOO2_PRE_DESTINO
    assert len(r["voos"])>0

    data_dt = time.strptime(r["data"][:10], "%Y-%m-%d")
    for v in r["voos"]:
        assert v["aeroporto_origem"]["codigo"] == VOO2_PRE_ORIGEM
        assert v["aeroporto_destino"]["codigo"] == VOO2_PRE_DESTINO
        v_dt =  time.strptime(v["data"][:10], "%Y-%m-%d")
        assert v_dt > data_dt

    inserir_ou_alterar_cache( [ 
        ("voo2", r["voos"][0]["codigo"])
    ] )

    ###### 3o voo
    params = {
        "data": data_voo_str,
        "origem": VOO3_PRE_ORIGEM,
        "destino": VOO3_PRE_DESTINO
    }
    resp = requests.get(URL + f"/voos", 
                         headers=HEADERS, params=params)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["origem"]==VOO3_PRE_ORIGEM and r["destino"]==VOO3_PRE_DESTINO
    assert len(r["voos"])>0

    data_dt = time.strptime(r["data"][:10], "%Y-%m-%d")
    for v in r["voos"]:
        assert v["aeroporto_origem"]["codigo"] == VOO3_PRE_ORIGEM
        assert v["aeroporto_destino"]["codigo"] == VOO3_PRE_DESTINO
        v_dt =  time.strptime(v["data"][:10], "%Y-%m-%d")
        assert v_dt > data_dt

    inserir_ou_alterar_cache( [ 
        ("voo3", r["voos"][0]["codigo"])
    ] )


def test_r07_efetuar_reserva1():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    voo = cache["voo1"]
    milhas1 = int(cache["milhas1"])
    milhas2 = int(cache["milhas2"])
    saldo_milhas = int(cache["saldo_milhas"])

    milhas_usadas = random.randint(100, milhas1-500)
    milhas_depois_uso = saldo_milhas - milhas_usadas

    reserva = {
            "valor": 250.00,
            "milhas_utilizadas": milhas_usadas,
            "quantidade_poltronas": 1,
            "codigo_cliente": codigo,
            "codigo_voo": voo
    }
    resp = requests.post(URL + f"/reservas", 
                         headers=HEADERS,
                         json=reserva)
    
    assert resp.status_code==201

    r = resp.json()
    assert r["codigo_cliente"]==codigo and r["estado"]=="CRIADA"
    assert r["voo"]["codigo"]==voo
    assert r["voo"]["aeroporto_origem"]["codigo"]==VOO1_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"]==VOO1_PRE_DESTINO

    inserir_ou_alterar_cache([ 
        ("reserva1", r["codigo"]),
        ("milhas_usadas1", milhas_usadas),
        ("saldo_milhas", milhas_depois_uso)
    ])

    # Verifica se as milhas foram descontadas
    resp = requests.get(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS)

    assert resp.status_code==200
    
    r = resp.json()
    assert r["codigo"]==codigo
    assert r["saldo_milhas"] == milhas_depois_uso


def test_r07_efetuar_reserva2():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    voo = cache["voo2"]
    milhas1 = int(cache["milhas1"])
    milhas2 = int(cache["milhas2"])
    saldo_milhas = int(cache["saldo_milhas"])
    milhas_usadas = random.randint(100, 200)
    milhas_depois_uso = saldo_milhas - milhas_usadas

    reserva = {
            "valor": 100.00,
            "milhas_utilizadas": milhas_usadas,
            "quantidade_poltronas": 1,
            "codigo_cliente": codigo,
            "codigo_voo": voo,
            "codigo_aeroporto_origem": VOO2_PRE_ORIGEM,
            "codigo_aeroporto_destino": VOO2_PRE_DESTINO
    }
    resp = requests.post(URL + f"/reservas", 
                         headers=HEADERS,
                         json=reserva)
    
    assert resp.status_code==201

    r = resp.json()
    assert r["codigo_cliente"]==codigo and r["estado"]=="CRIADA"
    assert r["voo"]["codigo"]==voo
    assert r["voo"]["aeroporto_origem"]["codigo"]==VOO2_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"]==VOO2_PRE_DESTINO

    inserir_ou_alterar_cache([ 
        ("reserva2", r["codigo"]),
        ("milhas_usadas2", milhas_usadas),
        ("saldo_milhas", milhas_depois_uso)
    ])

    # Verifica se as milhas foram descontadas
    resp = requests.get(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS)

    assert resp.status_code==200
    
    r = resp.json()
    assert r["codigo"]==codigo
    assert r["saldo_milhas"] == milhas_depois_uso


def test_r07_efetuar_reserva3():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    voo = cache["voo3"]
    milhas1 = int(cache["milhas1"])
    milhas2 = int(cache["milhas2"])
    saldo_milhas = int(cache["saldo_milhas"])
    milhas_usadas = random.randint(100, 200)
    milhas_depois_uso = saldo_milhas - milhas_usadas

    reserva = {
            "valor": 50.00,
            "milhas_utilizadas": milhas_usadas,
            "quantidade_poltronas": 1,
            "codigo_cliente": codigo,
            "codigo_voo": voo,
            "codigo_aeroporto_origem": VOO3_PRE_ORIGEM,
            "codigo_aeroporto_destino": VOO3_PRE_DESTINO
    }
    resp = requests.post(URL + f"/reservas", 
                         headers=HEADERS,
                         json=reserva)
    
    assert resp.status_code==201

    r = resp.json()
    assert r["codigo_cliente"]==codigo and r["estado"]=="CRIADA"
    assert r["voo"]["codigo"]==voo
    assert r["voo"]["aeroporto_origem"]["codigo"]==VOO3_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"]==VOO3_PRE_DESTINO

    inserir_ou_alterar_cache([ 
        ("reserva3", r["codigo"]),
        ("milhas_usadas3", milhas_usadas),
        ("saldo_milhas", milhas_depois_uso)
    ])

def test_r07_efetuar_reserva_nao_embarcar():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    voo = cache["voo2"]
    milhas1 = int(cache["milhas1"])
    milhas2 = int(cache["milhas2"])
    saldo_milhas = int(cache["saldo_milhas"])
    milhas_usadas = random.randint(10, 20)
    milhas_depois_uso = saldo_milhas - milhas_usadas

    reserva = {
            "valor": 50.00,
            "milhas_utilizadas": milhas_usadas,
            "quantidade_poltronas": 1,
            "codigo_cliente": codigo,
            "codigo_voo": voo,
            "codigo_aeroporto_origem": VOO2_PRE_ORIGEM,
            "codigo_aeroporto_destino": VOO2_PRE_DESTINO
    }
    resp = requests.post(URL + f"/reservas", 
                         headers=HEADERS,
                         json=reserva)
    
    assert resp.status_code==201

    r = resp.json()
    assert r["codigo_cliente"]==codigo and r["estado"]=="CRIADA"
    assert r["voo"]["codigo"]==voo
    assert r["voo"]["aeroporto_origem"]["codigo"]==VOO2_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"]==VOO2_PRE_DESTINO

    inserir_ou_alterar_cache([ 
        ("reserva_nao_embarcar", r["codigo"]),
        ("milhas_usadas_nao_embarcar", milhas_usadas),
        ("saldo_milhas", milhas_depois_uso)
    ])


    # Verifica se as milhas foram descontadas
    resp = requests.get(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS)

    assert resp.status_code==200
    
    r = resp.json()
    assert r["codigo"]==codigo
    assert r["saldo_milhas"] == milhas_depois_uso


def test_r07_efetuar_reserva_milhas_insuficientes():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    voo = cache["voo3"]

    reserva = {
            "valor": 50.00,
            "milhas_utilizadas": 100000,
            "quantidade_poltronas": 1,
            "codigo_cliente": codigo,
            "codigo_voo": voo,
            "codigo_aeroporto_origem": VOO3_PRE_ORIGEM,
            "codigo_aeroporto_destino": VOO3_PRE_DESTINO
    }
    resp = requests.post(URL + f"/reservas", 
                         headers=HEADERS,
                         json=reserva)
    
    assert resp.status_code==400

    r = resp.json()
    assert r["erro"]=="Saldo de milhas insuficiente"

def test_r07_efetuar_reserva_milhas_insuficientes_1_a_mais():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    voo = cache["voo3"]

    resp = requests.get(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    milhas = r["saldo_milhas"]

    milhas = milhas + 1 # para dar insuficiente

    reserva = {
            "valor": 50.00,
            "milhas_utilizadas": milhas,
            "quantidade_poltronas": 1,
            "codigo_cliente": codigo,
            "codigo_voo": voo,
            "codigo_aeroporto_origem": VOO3_PRE_ORIGEM,
            "codigo_aeroporto_destino": VOO3_PRE_DESTINO
    }
    resp = requests.post(URL + f"/reservas", 
                         headers=HEADERS,
                         json=reserva)
    
    assert resp.status_code==400

    r = resp.json()
    assert r["erro"]=="Saldo de milhas insuficiente"


def test_r07_efetuar_reserva_todas_as_milhas_usadas():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["cliente_codigo"]
    voo = cache["voo3"]

    resp = requests.get(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    milhas = r["saldo_milhas"]

    reserva = {
            "valor": 50.00,
            "milhas_utilizadas": milhas,
            "quantidade_poltronas": 1,
            "codigo_cliente": codigo,
            "codigo_voo": voo,
            "codigo_aeroporto_origem": VOO3_PRE_ORIGEM,
            "codigo_aeroporto_destino": VOO3_PRE_DESTINO
    }
    resp = requests.post(URL + f"/reservas", 
                         headers=HEADERS,
                         json=reserva)
    
    assert resp.status_code==201

    r = resp.json()
    assert r["codigo_cliente"]==codigo and r["estado"]=="CRIADA"
    assert r["voo"]["codigo"]==voo
    assert r["voo"]["aeroporto_origem"]["codigo"]==VOO3_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"]==VOO3_PRE_DESTINO

    resp = requests.get(URL + f"/clientes/{codigo}/milhas", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["saldo_milhas"]==0




####################################################
# R09 - Consultar Reserva

def test_r09_consulta_reserva1():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()

    reserva1 = cache["reserva1"]
    voo1 = cache["voo1"]
    codigo = cache["cliente_codigo"]

    ####### Reserva 1
    resp = requests.get(URL + f"/reservas/{reserva1}", 
                         headers=HEADERS)
    
    r = resp.json()
    assert resp.status_code==200
    assert r["codigo"]==reserva1
    assert r["codigo_cliente"]==codigo
    assert r["estado"] == "CRIADA"
    assert r["voo"]["codigo"] == voo1
    assert r["voo"]["aeroporto_origem"]["codigo"] == VOO1_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"] == VOO1_PRE_DESTINO

def test_r09_consulta_reserva2():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()

    reserva2 = cache["reserva2"]
    voo2 = cache["voo2"]
    codigo = cache["cliente_codigo"]

    resp = requests.get(URL + f"/reservas/{reserva2}", 
                         headers=HEADERS)
    
    r = resp.json()
    assert resp.status_code==200
    assert r["codigo"]==reserva2
    assert r["codigo_cliente"]==codigo
    assert r["estado"] == "CRIADA"
    assert r["voo"]["codigo"] == voo2
    assert r["voo"]["aeroporto_origem"]["codigo"] == VOO2_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"] == VOO2_PRE_DESTINO


def test_r09_consulta_reserva3():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()

    reserva3 = cache["reserva3"]
    voo3 = cache["voo3"]
    codigo = cache["cliente_codigo"]

    ####### Reserva 3
    resp = requests.get(URL + f"/reservas/{reserva3}", 
                         headers=HEADERS)
    
    r = resp.json()
    assert resp.status_code==200
    assert r["codigo"]==reserva3
    assert r["codigo_cliente"]==codigo
    assert r["estado"] == "CRIADA"
    assert r["voo"]["codigo"] == voo3
    assert r["voo"]["aeroporto_origem"]["codigo"] == VOO3_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"] == VOO3_PRE_DESTINO


####################################################
# HELPER - Verifica estado da reserva
#          Espera 2s e então busca a reserva
#          Se não retornou o estado desejado, pode ser
#          que o CQRS não atualizou, então tenta mais
#          3 vezes com intervalo de 5s
#          Se mesmo assim não der, requisito não atendido
# Parâmetros:
#     codigo: código da reserva
#     cliente: código do cliente
#     estado: string com o estado desejado
def verificar_estado_reserva(codigo, cliente, estado):

    # espera para dar tempo ao CQRS
    time.sleep(2)
    resp = requests.get(URL + f"/reservas/{codigo}", 
                         headers=HEADERS)    
    r = resp.json()
    assert resp.status_code==200
    assert r["codigo"]==codigo
    assert r["codigo_cliente"]==cliente

    # Tenta mais 3 vezes
    tentativas = 3
    tent = 0
    while r["estado"] != estado and tent < tentativas:
        time.sleep(5)
        resp = requests.get(URL + f"/reservas/{codigo}", 
                            headers=HEADERS)
        
        r = resp.json()
        assert resp.status_code==200
        assert r["codigo"]==codigo
        assert r["codigo_cliente"]==cliente
        tent += 1
        
    assert r["estado"] == estado

    return r


####################################################
# R08 - Cancelar Reserva

def test_r08_cancelar_reserva1():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()

    reserva = cache["reserva1"]
    codigo = cache["cliente_codigo"]

    # Efetua o cancelamento da reserva1
    resp = requests.delete(URL + f"/reservas/{reserva}", 
                         headers=HEADERS)
    
    r = resp.json()
    assert resp.status_code==200
    assert r["codigo"]==reserva
    #assert r["codigo_cliente"]==codigo and r["estado"]=="CANCELADA"

    verificar_estado_reserva(reserva, codigo, "CANCELADA")


####################################################
# R10 - Check-in

def test_r10_checkin_reserva2():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()

    reserva = cache["reserva2"]
    codigo = cache["cliente_codigo"]

    estado = { "estado" : "CHECK-IN"}
    resp = requests.patch(URL + f"/reservas/{reserva}/estado", 
                         headers=HEADERS,
                         json=estado)
    
    r = resp.json()
    assert resp.status_code==200
    assert r["codigo"]==reserva
    assert r["codigo_cliente"]==codigo and r["estado"]=="CHECK-IN"


    verificar_estado_reserva(reserva, codigo, "CHECK-IN")


####################################################
# R02 - Tela inicial do usuário, buscar voos em 48h

def test_r02_login_funcionario():

    login = {
        "login" : EMAIL_FUNC_PRE,
        "senha" : SENHA_FUNC_PRE
    }
    resp = requests.post(URL + "/login", 
                         headers=HEADERS, 
                         json=login)
    
    assert resp.status_code==200 

    r = resp.json()
    assert "access_token" in r
    assert "token_type" in r
    assert r["tipo"] == "FUNCIONARIO"
    assert r["usuario"]["cpf"] == CPF_FUNC_PRE
    assert r["usuario"]["email"] == EMAIL_FUNC_PRE

    inserir_ou_alterar_cache([ ("func1", r["usuario"]["codigo"]) ])

    ACCESS_TOKEN = r["access_token"]
    # Adiciona o token retornado para as próximas chamadas
    salvar_token(f"Bearer {ACCESS_TOKEN}")



####################################################
# R11 - Tela inicial do usuário, buscar voos em 48h

def test_r11_buscar_proximos_voos():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    inicio = "2025-08-09"
    fim = "2025-08-11"
    params = {
        "inicio": inicio,
        "fim": fim
    }
    resp = requests.get(URL + f"/voos", 
                         headers=HEADERS, params=params)
    
    r = resp.json()

    assert resp.status_code==200
    assert r["inicio"]==inicio and r["fim"]==fim
    assert len(r["voos"])>0

    inicio_dt = time.strptime(inicio, "%Y-%m-%d")
    fim_dt = time.strptime(fim, "%Y-%m-%d")
    for v in r["voos"]:
        v_dt =  time.strptime(v["data"][:10], "%Y-%m-%d")
        assert v_dt >= inicio_dt and v_dt <= fim_dt


####################################################
# R15 - Inserir Novo Voo

def test_r15_inserir_voo1():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    agora = datetime.now()
    delta = timedelta(days=1)
    data_voo = agora + delta
    data_voo_str = data_voo.strftime("%Y-%m-%dT%H:%M:%S-03:00")

    novo_voo = {
        "data": data_voo_str, 
        "valor_passagem": 111.00,
        "quantidade_poltronas_total": 111,
        "quantidade_poltronas_ocupadas": 11,
        "codigo_aeroporto_origem": VOO1_ORIGEM,
        "codigo_aeroporto_destino": VOO1_DESTINO
    }
    resp = requests.post(URL + f"/voos", 
                         headers=HEADERS,
                         json=novo_voo)
    
    assert resp.status_code==201

    r = resp.json()
    codigo = r["codigo"]
    assert r["estado"]=="CONFIRMADO"

    inserir_ou_alterar_cache([ ("novo_voo1", codigo) ])

    resp = requests.get(URL + f"/voos/{codigo}", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==codigo
    assert r["estado"]=="CONFIRMADO"
    assert r["aeroporto_origem"]["codigo"]==VOO1_ORIGEM
    assert r["aeroporto_destino"]["codigo"]==VOO1_DESTINO

    # resp.json() retornando data convertida para UTC??
    # data_r = datetime.strptime(r["data"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=3)
    # data_voo = datetime.strptime(data_voo_str, "%Y-%m-%dT%H:%M:%S-03:00") 
    # assert data_r == data_voo_str

    assert r["data"] == data_voo_str

def test_r15_inserir_voo2():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    agora = datetime.now()
    delta = timedelta(days=1, minutes=30)
    data_voo = agora + delta
    data_voo_str = data_voo.strftime("%Y-%m-%dT%H:%M:%S-03:00")

    novo_voo = {
        "data": data_voo_str, 
        "valor_passagem": 222.00,
        "quantidade_poltronas_total": 222,
        "quantidade_poltronas_ocupadas": 22,
        "codigo_aeroporto_origem": VOO2_ORIGEM,
        "codigo_aeroporto_destino": VOO2_DESTINO
    }
    resp = requests.post(URL + f"/voos", 
                         headers=HEADERS,
                         json=novo_voo)
    
    assert resp.status_code==201

    r = resp.json()
    codigo = r["codigo"]
    assert r["estado"]=="CONFIRMADO"

    inserir_ou_alterar_cache([ ("novo_voo2", codigo) ])

    resp = requests.get(URL + f"/voos/{codigo}", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==codigo
    assert r["estado"]=="CONFIRMADO"
    assert r["aeroporto_origem"]["codigo"]==VOO2_ORIGEM
    assert r["aeroporto_destino"]["codigo"]==VOO2_DESTINO

    # print("!!! r15 - inserir voo 1 - ver a comparação de datas")
    # data_r = datetime.strptime(r["data"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=3)
    # data_voo = datetime.strptime(data_voo_str, "%Y-%m-%dT%H:%M:%S-03:00") 
    # assert data_r == data_voo_str

    assert r["data"] == data_voo_str

def test_r15_inserir_voo3():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    agora = datetime.now()
    delta = timedelta(days=5, minutes=30)
    data_voo = agora + delta
    data_voo_str = data_voo.strftime("%Y-%m-%dT%H:%M:%S-03:00")

    novo_voo = {
        "data": data_voo_str, 
        "valor_passagem": 333.00,
        "quantidade_poltronas_total": 333,
        "quantidade_poltronas_ocupadas": 133,
        "codigo_aeroporto_origem": VOO3_ORIGEM,
        "codigo_aeroporto_destino": VOO3_DESTINO
    }
    resp = requests.post(URL + f"/voos", 
                         headers=HEADERS,
                         json=novo_voo)
    
    assert resp.status_code==201

    r = resp.json()
    codigo = r["codigo"]
    assert r["estado"]=="CONFIRMADO"

    inserir_ou_alterar_cache([ ("novo_voo3", codigo) ])

    resp = requests.get(URL + f"/voos/{codigo}", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==codigo
    assert r["estado"]=="CONFIRMADO"
    assert r["aeroporto_origem"]["codigo"]==VOO3_ORIGEM
    assert r["aeroporto_destino"]["codigo"]==VOO3_DESTINO

    # print("!!! r15 - inserir voo 1 - ver a comparação de datas")
    # data_r = datetime.strptime(r["data"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=3)
    # data_voo = datetime.strptime(data_voo_str, "%Y-%m-%dT%H:%M:%S-03:00") 
    # assert data_r == data_voo_str

    assert r["data"] == data_voo_str


####################################################
# R12 - Confirmação de Embarque

def test_r12_confirmacao_embarque():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()

    reserva = cache["reserva2"]
    codigo = cache["cliente_codigo"]

    estado = { "estado" : "EMBARCADA"}
    resp = requests.patch(URL + f"/reservas/{reserva}/estado", 
                         headers=HEADERS,
                         json=estado)
    
    assert resp.status_code==200
    r = resp.json()
    assert r["codigo"]==reserva
    assert r["codigo_cliente"]==codigo and r["estado"]=="EMBARCADA"

    verificar_estado_reserva(reserva, codigo, "EMBARCADA")


####################################################
# R13 - Cancelamento Voo

def test_r13_cancelamento_voo():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    reserva = cache["reserva3"]
    codigo = cache["cliente_codigo"]
    voo = cache["voo3"]

    estado = { "estado" : "CANCELADO"}
    resp = requests.patch(URL + f"/voos/{voo}/estado", 
                         headers=HEADERS,
                         json=estado)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==voo
    assert r["estado"]=="CANCELADO"

    resp = requests.get(URL + f"/voos/{voo}", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==voo
    assert r["estado"]=="CANCELADO"

    ####### Verifica se a Reserva3 foi cancelada

    r = verificar_estado_reserva(reserva, codigo, "CANCELADA VOO")

    assert r["voo"]["codigo"] == voo
    assert r["voo"]["aeroporto_origem"]["codigo"] == VOO3_PRE_ORIGEM
    assert r["voo"]["aeroporto_destino"]["codigo"] == VOO3_PRE_DESTINO
    

####################################################
# R14 - Realização Voo

def test_r14_realizacao_voo():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    reserva = cache["reserva2"]
    reserva_nao_embarcar = cache["reserva_nao_embarcar"]
    codigo = cache["cliente_codigo"]
    voo = cache["voo2"]

    ### Troca o estado do VOO
    estado = { "estado" : "REALIZADO"}
    resp = requests.patch(URL + f"/voos/{voo}/estado", 
                         headers=HEADERS,
                         json=estado)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==voo
    assert r["estado"]=="REALIZADO"

    ### Verifica se o VOO2 passou para REALIZADO
    resp = requests.get(URL + f"/voos/{voo}", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["codigo"]==voo
    assert r["estado"]=="REALIZADO"

    r = verificar_estado_reserva(reserva, codigo, "REALIZADA")

    ### Verifica se a Reserva não embarcada do Voo2 passou para NÃO REALIZADA
    r = verificar_estado_reserva(reserva_nao_embarcar, codigo, "NÃO REALIZADA")


####################################################
# R16 - Listagem de Funcionários

def test_r16_listar_funcionarios():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    resp = requests.get(URL + f"/funcionarios", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    for v in r:
        assert v["tipo"] == "FUNCIONARIO"
        

####################################################
# R17 - Inserir Funcionário

def test_r17_inserir_funcionario1():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    ### Insere FUNCIONARIO1
    cpf = gerar_cpf()
    email = gerar_email()
    senha = gerar_senha()
    FUNCIONARIO1["cpf"] = cpf
    FUNCIONARIO1["email"] = email
    FUNCIONARIO1["senha"] = senha
    resp = requests.post(URL + f"/funcionarios", 
                         headers=HEADERS,
                         json=FUNCIONARIO1)
    

    assert resp.status_code==201

    r = resp.json()
    assert r["cpf"]==cpf

    inserir_ou_alterar_cache([ 
        ("funcionario1_codigo", r["codigo"]),
        ("funcionario1_cpf", cpf),
        ("funcionario1_email", email),
        ("funcionario1_senha", senha),
    ])

def test_r17_inserir_funcionario2():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    ### Insere FUNCIONARIO1
    cpf = gerar_cpf()
    email = gerar_email()
    senha = gerar_senha()
    FUNCIONARIO2["cpf"] = cpf
    FUNCIONARIO2["email"] = email
    FUNCIONARIO2["senha"] = senha
    resp = requests.post(URL + f"/funcionarios", 
                         headers=HEADERS,
                         json=FUNCIONARIO2)
    

    assert resp.status_code==201

    r = resp.json()
    assert r["cpf"]==cpf

    inserir_ou_alterar_cache([ 
        ("funcionario2_codigo", r["codigo"]),
        ("funcionario2_cpf", cpf),
        ("funcionario2_email", email),
        ("funcionario2_senha", senha),
    ])


def test_r17_logout_funcionario():
    token = recuperar_token()
    HEADERS["Authorization"] = token
    
    cache = recuperar_cache()
    email = cache["cliente_email"]

    LOGOUT = {
        "login" : email
    }
    resp = requests.post(URL + "/logout", 
                         headers=HEADERS, 
                         json=LOGOUT)
    
    assert resp.status_code==200

    salvar_token(f"")

def test_r17_login_funcionario_novo():
    cache = recuperar_cache()
    email = cache["funcionario1_email"]
    senha = cache["funcionario1_senha"]
    codigo = cache["funcionario1_codigo"]
    cpf = cache["funcionario1_cpf"]

    LOGIN["login"] = email
    LOGIN["senha"] = senha

    resp = requests.post(URL + "/login", 
                         headers=HEADERS, 
                         json=LOGIN)
    
    assert resp.status_code==200 

    r = resp.json()
    assert "access_token" in r
    assert "token_type" in r
    assert r["usuario"]["codigo"] == codigo
    assert r["usuario"]["cpf"] == cpf
    assert r["usuario"]["email"] == email
    assert r["tipo"] == "FUNCIONARIO"

    ACCESS_TOKEN = r["access_token"]

    # Adiciona o token retornado para as próximas chamadas
    salvar_token(f"Bearer {ACCESS_TOKEN}")


####################################################
# R18 - Atualizar Funcionário

def test_r18_atualizar_funcionario():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["funcionario1_codigo"]
    email = cache["funcionario1_email"]
    cpf = cache["funcionario1_cpf"]
    email_novo = gerar_email()

    # Recupera funcionário antigo e verifica que realmente está com email antigo
    resp = requests.get(URL + f"/funcionarios/{codigo}", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["cpf"]==cpf
    assert r["email"]==email


    # Troca para o novo e-mail
    FUNCIONARIO1["cpf"] = cpf
    FUNCIONARIO1["email"] = email_novo
    FUNCIONARIO1["nome"] = "Novo Nome Alterado"

    resp = requests.put(URL + f"/funcionarios/{codigo}", 
                         headers=HEADERS,
                         json=FUNCIONARIO1)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["cpf"]==cpf
    assert r["email"]==email_novo
    assert r["nome"]=="Novo Nome Alterado"

    # Recupera funcionário e verifica que realmente alterou o e-mail
    resp = requests.get(URL + f"/funcionarios/{codigo}", 
                         headers=HEADERS)
    
    assert resp.status_code==200

    r = resp.json()
    assert r["cpf"]==cpf
    assert r["email"]==email_novo
    assert r["nome"]=="Novo Nome Alterado"


####################################################
# R19 - Remover Funcionário

def test_r19_remover_funcionario():
    token = recuperar_token()
    HEADERS["Authorization"] = token

    cache = recuperar_cache()
    codigo = cache["funcionario2_codigo"]
    cpf = cache["funcionario2_cpf"]
    resp = requests.delete(URL + f"/funcionarios/{codigo}", 
                         headers=HEADERS)
    

    assert resp.status_code==200

    r = resp.json()
    assert r["cpf"]==cpf

    resp = requests.get(URL + f"/funcionarios/{codigo}", 
                         headers=HEADERS)
    
    assert resp.status_code==404
