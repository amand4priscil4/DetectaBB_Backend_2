import requests
import json

base_url = "http://localhost:5000"

def testar_registro():
    print("=== TESTE DE REGISTRO ===")
    dados = {
        "nome": "João Silva",
        "email": "joao@teste.com", 
        "senha": "123456"
    }
    
    response = requests.post(f"{base_url}/api/auth/register", json=dados)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    print()
    
    # Retorna True se registrou OU se já existe
    return response.status_code == 201 or response.status_code == 400

def testar_login():
    print("=== TESTE DE LOGIN ===")
    dados = {
        "email": "joao@teste.com",
        "senha": "123456"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=dados)
    print(f"Status: {response.status_code}")
    resultado = response.json()
    print(f"Resposta: {resultado}")
    print()
    
    if response.status_code == 200:
        return resultado.get("token")
    return None

def testar_analise_com_auth(token):
    print("=== TESTE ANÁLISE COM AUTENTICAÇÃO ===")
    headers = {"Authorization": f"Bearer {token}"}
    dados = {
        "banco": "Itaú",
        "codigo_banco": 341,
        "agencia": 5678,
        "valor": 2500.75,
        "linha_digitavel": "34191234567890123456789012345678901"
    }
    
    response = requests.post(f"{base_url}/api/analyze", json=dados, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        resultado = response.json()
        print(f"Predição: {resultado['resultado']['predicao']}")
        print(f"Confiança: {resultado['resultado']['confianca']:.2%}")
        print(f"User ID: {resultado.get('user_id')}")
    else:
        print(f"Erro: {response.json()}")
    print()

def main():
    print("🔐 TESTANDO SISTEMA DE AUTENTICAÇÃO")
    print("=" * 50)
    
    # Teste 1: Registrar usuário (ou confirmar que já existe)
    if testar_registro():
        print("✅ Usuário disponível para login")
    else:
        print("❌ Falha no registro")
        return
    
    # Teste 2: Fazer login
    token = testar_login()
    if token:
        print("✅ Login bem-sucedido")
        # Teste 3: Análise com autenticação
        testar_analise_com_auth(token)
    else:
        print("❌ Falha no login")

if __name__ == "__main__":
    main()