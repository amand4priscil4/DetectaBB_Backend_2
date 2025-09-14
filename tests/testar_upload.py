import requests

base_url = "http://localhost:5000"

def testar_limites():
    print("=== TESTE DE LIMITES ===")
    response = requests.get(f"{base_url}/api/upload/limits")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    print()

def testar_upload_sem_arquivo():
    print("=== TESTE UPLOAD SEM ARQUIVO ===")
    response = requests.post(f"{base_url}/api/upload/analyze-file")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    print()

if __name__ == "__main__":
    print("🔄 TESTANDO SISTEMA DE UPLOAD")
    print("=" * 50)
    
    testar_limites()
    testar_upload_sem_arquivo()