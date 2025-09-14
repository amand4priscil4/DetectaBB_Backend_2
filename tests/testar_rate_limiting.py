import requests
import time

base_url = "http://localhost:5000"

def testar_rate_limit_upload():
    print("=== TESTE RATE LIMIT UPLOAD (10/min) ===")
    
    for i in range(12):  # Mais que o limite de 10
        response = requests.get(f"{base_url}/api/upload/limits")
        print(f"Request {i+1}: Status {response.status_code}")
        
        if response.status_code == 429:
            resultado = response.json()
            print(f"BLOQUEADO: {resultado['error']}")
            break
        
        time.sleep(1)  # 1 segundo entre requests

def testar_rate_limit_register():
    print("\n=== TESTE RATE LIMIT REGISTRO (5/min) ===")
    
    for i in range(7):  # Mais que o limite de 5
        dados = {
            "nome": f"Usuario {i}",
            "email": f"usuario{i}@teste.com",
            "senha": "MinhaSenh@123!"
        }
        
        response = requests.post(f"{base_url}/api/auth/register", json=dados)
        print(f"Registro {i+1}: Status {response.status_code}")
        
        if response.status_code == 429:
            resultado = response.json()
            print(f"BLOQUEADO: {resultado['error']}")
            break
        elif response.status_code == 400:
            resultado = response.json()
            if "já cadastrado" in resultado.get('error', ''):
                print(f"Email já existe - continuando...")
            else:
                print(f"Erro: {resultado['error']}")
        
        time.sleep(1)

if __name__ == "__main__":
    testar_rate_limit_upload()
    testar_rate_limit_register()