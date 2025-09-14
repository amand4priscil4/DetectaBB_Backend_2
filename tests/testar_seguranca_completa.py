import requests

base_url = "http://localhost:5000/api/auth"

def testar_senhas():
    print("=== TESTE VALIDAÇÃO DE SENHAS ===")
    
    testes = [
        ("123456", "Muito curta"),
        ("senhasemnum", "Sem número"),
        ("SENHASEMMINUS", "Sem minúscula"), 
        ("senhasemmaiuscula123", "Sem maiúscula"),
        ("SenhaSegura123", "Sem caractere especial"),
        ("MinhaSenh@Segura123!", "Senha forte - deve aceitar")
    ]
    
    for i, (senha, descricao) in enumerate(testes):
        dados = {
            "nome": f"Teste {i}",
            "email": f"teste{i}@exemplo.com",
            "senha": senha
        }
        
        response = requests.post(f"{base_url}/register", json=dados)
        
        if response.status_code == 201:
            print(f"✅ {descricao}: ACEITA")
        else:
            erro = response.json().get('error', 'Erro desconhecido')
            print(f"❌ {descricao}: REJEITADA - {erro}")

def testar_protecao_brute_force():
    print("\n=== TESTE PROTEÇÃO FORÇA BRUTA ===")
    
    dados = {
        "email": "inexistente@teste.com",
        "senha": "senhaerrada"
    }
    
    for i in range(7):
        response = requests.post(f"{base_url}/login", json=dados)
        resultado = response.json()
        
        print(f"Tentativa {i+1}: Status {response.status_code}")
        
        if response.status_code == 429:
            print(f"🛡️ PROTEÇÃO ATIVADA: {resultado['error']}")
            break
        elif "attempts_remaining" in resultado:
            print(f"   Tentativas restantes: {resultado['attempts_remaining']}")

if __name__ == "__main__":
    testar_senhas()
    testar_protecao_brute_force()