import requests
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

base_url = "http://localhost:5000"

def fazer_login():
    """Faz login e retorna token"""
    dados = {
        "email": "joao@teste.com",
        "senha": "123456"
    }
    response = requests.post(f"{base_url}/api/auth/login", json=dados)
    if response.status_code == 200:
        return response.json()["token"]
    return None

def criar_pdf_boleto():
    """Cria PDF de teste"""
    filename = "boleto_auth_teste.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 100, "BANCO ITAU S.A.")
    c.drawString(100, height - 140, "Linha Digitável: 34191.23456 78901.234567 89012.345678 9 87654321098765")
    c.drawString(100, height - 180, "Valor: R$ 2.500,00")
    c.drawString(100, height - 220, "Vencimento: 20/12/2024")
    
    c.save()
    return filename

def testar_upload_autenticado():
    print("=== TESTE UPLOAD COM AUTENTICAÇÃO ===")
    
    # Fazer login
    token = fazer_login()
    if not token:
        print("Erro no login")
        return
    
    # Criar PDF
    pdf_file = criar_pdf_boleto()
    
    try:
        # Headers com token
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file, f, 'application/pdf')}
            response = requests.post(f"{base_url}/api/upload/analyze-file", 
                                   files=files, headers=headers)
        
        print(f"Status: {response.status_code}")
        resultado = response.json()
        
        if response.status_code == 200:
            print("Upload autenticado bem-sucedido!")
            print(f"User ID: {resultado['user_id']}")
            print(f"Banco: {resultado['dados_extraidos']['banco']}")
            print(f"Predição: {resultado['resultado_ml']['predicao']}")
            print(f"Confiança: {resultado['resultado_ml']['confianca']:.2%}")
            print(f"Limite usado: {resultado['limite_info']['usado_hoje']}/{resultado['limite_info']['limite_diario']}")
        else:
            print(f"Erro: {resultado}")
    
    finally:
        if os.path.exists(pdf_file):
            os.remove(pdf_file)

def verificar_historico_pessoal():
    print("\n=== HISTÓRICO PESSOAL ===")
    token = fazer_login()
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/history", headers=headers)
        resultado = response.json()
        print(f"Total de análises: {resultado['total']}")
        if resultado['analises']:
            print("Últimas análises:")
            for analise in resultado['analises'][:3]:
                print(f"- ID {analise['id']}: {analise['resultado']['predicao']} ({analise['dados_entrada']['banco']})")

if __name__ == "__main__":
    print("🔐 TESTANDO UPLOAD COM AUTENTICAÇÃO")
    print("=" * 50)
    
    testar_upload_autenticado()
    verificar_historico_pessoal()