import requests
import os

base_url = "http://localhost:5000"

def testar_upload_com_arquivo():
    print("=== TESTE UPLOAD COM ARQUIVO ===")
    
    # Criar um arquivo de texto simples para testar (simula um boleto)
    conteudo_boleto = """
    BANCO DO BRASIL S.A.
    Linha Digitável: 00190.00009 01234.567890 12345.678901 2 12345678901234
    Valor: R$ 1.250,75
    Vencimento: 15/12/2024
    """
    
    # Salvar como arquivo temporário
    with open('boleto_teste.txt', 'w', encoding='utf-8') as f:
        f.write(conteudo_boleto)
    
    try:
        # Fazer upload do arquivo
        with open('boleto_teste.txt', 'rb') as f:
            files = {'file': ('boleto_teste.txt', f, 'text/plain')}
            response = requests.post(f"{base_url}/api/upload/analyze-file", files=files)
        
        print(f"Status: {response.status_code}")
        resultado = response.json()
        
        if response.status_code == 200:
            print("Upload bem-sucedido!")
            print(f"Arquivo: {resultado['arquivo_processado']['nome_arquivo']}")
            print(f"Predição: {resultado['resultado_ml']['predicao']}")
            print(f"Confiança: {resultado['resultado_ml']['confianca']:.2%}")
            print(f"Dados extraídos: {resultado['dados_extraidos']}")
        else:
            print(f"Erro: {resultado}")
    
    finally:
        # Limpar arquivo temporário
        if os.path.exists('boleto_teste.txt'):
            os.remove('boleto_teste.txt')

def testar_limites_apos_upload():
    print("\n=== TESTE LIMITES APÓS UPLOAD ===")
    response = requests.get(f"{base_url}/api/upload/limits")
    resultado = response.json()
    print(f"Usado hoje: {resultado['limite_atual']['usado_hoje']}")
    print(f"Restante: {resultado['limite_atual']['restante']}")

if __name__ == "__main__":
    print("TESTANDO UPLOAD DE ARQUIVO")
    print("=" * 50)
    
    testar_upload_com_arquivo()
    testar_limites_apos_upload()