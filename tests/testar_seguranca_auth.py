import requests

base_url = "http://localhost:5000/api/auth"

def testar_senha_fraca():
    print("=== TESTE SENHA FRACA ===")
    dados = {
        "nome": "Teste",
        "email": "teste@exemplo.com",
        "senha": "123456"
    }
    response = requests.post(f"{base_url}/register", json=dados)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")

def testar_senha_forte():
    print("\n=== TESTE SENHA FORTE ===")
    dados = {
        "nome": "Teste Seguro",
        "email": "seguro@exemplo.com", 
        "senha": "MinhaSenh@123!"
    }
    response = requests.post(f"{base_url}/register", json=dados)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")

if __name__ == "__main__":
    testar_senha_fraca()
    testar_senha_forte()