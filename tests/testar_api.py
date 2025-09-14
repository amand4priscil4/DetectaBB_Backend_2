import requests
import json

base_url = "http://localhost:5000"

def testar_health():
    response = requests.get(f"{base_url}/api/health")
    print("Health Check:", response.json())

def testar_stats():
    response = requests.get(f"{base_url}/api/stats")
    print("Estatísticas:", response.json())

def testar_boleto(dados, nome_teste):
    response = requests.post(f"{base_url}/api/analyze", json=dados)
    print(f"\n{nome_teste}:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        resultado = response.json()
        print(f"Predição: {resultado['resultado']['predicao']}")
        print(f"Confiança: {resultado['resultado']['confianca']:.2%}")
    else:
        print("Erro:", response.json())

# Executar testes
if __name__ == "__main__":
    print("=== TESTANDO API ===")
    
    testar_health()
    testar_stats()
    
    # Teste 1: Banco do Brasil
    testar_boleto({
        "banco": "Banco do Brasil",
        "codigo_banco": 1,
        "agencia": 1234,
        "valor": 1000.50,
        "linha_digitavel": "00190000090012345678901234567890"
    }, "Teste 1 - Banco do Brasil")
    
    # Teste 2: Itaú
    testar_boleto({
        "banco": "Itaú",
        "codigo_banco": 341,
        "agencia": 5678,
        "valor": 2500.75,
        "linha_digitavel": "34191234567890123456789012345678901"
    }, "Teste 2 - Itaú")
    
    # Teste 3: Banco suspeito
    testar_boleto({
        "banco": "OLIVEIRA TRUST",
        "codigo_banco": 700,
        "agencia": 712,
        "valor": 834629.43,
        "linha_digitavel": "11100009001234567890123456789083462943"
    }, "Teste 3 - Banco suspeito")