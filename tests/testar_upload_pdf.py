import requests
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def criar_pdf_boleto():
    """Cria um PDF simples simulando um boleto"""
    filename = "boleto_teste.pdf"
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Adicionar texto do boleto
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 100, "BANCO DO BRASIL S.A.")
    c.drawString(100, height - 140, "Linha Digitável: 00190.00009 01234.567890 12345.678901 2 12345678901234")
    c.drawString(100, height - 180, "Valor: R$ 1.250,75")
    c.drawString(100, height - 220, "Vencimento: 15/12/2024")
    
    c.save()
    return filename

def testar_upload_pdf():
    print("=== TESTE UPLOAD PDF ===")
    
    # Criar PDF temporário
    pdf_file = criar_pdf_boleto()
    
    try:
        # Fazer upload
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file, f, 'application/pdf')}
            response = requests.post("http://localhost:5000/api/upload/analyze-file", files=files)
        
        print(f"Status: {response.status_code}")
        resultado = response.json()
        
        if response.status_code == 200:
            print("Upload PDF bem-sucedido!")
            print(f"Arquivo: {resultado['arquivo_processado']['nome_arquivo']}")
            print(f"Predição: {resultado['resultado_ml']['predicao']}")
            print(f"Confiança: {resultado['resultado_ml']['confianca']:.2%}")
            print(f"Dados extraídos: {resultado['dados_extraidos']}")
            if 'debug' in resultado:
                print(f"Texto extraído: {resultado['debug']['texto_extraido'][:200]}...")
        else:
            print(f"Erro: {resultado}")
    
    finally:
        # Limpar arquivo
        if os.path.exists(pdf_file):
            os.remove(pdf_file)

if __name__ == "__main__":
    # Instalar reportlab se necessário
    try:
        from reportlab.pdfgen import canvas
    except ImportError:
        print("Instalando reportlab...")
        os.system("pip install reportlab")
        from reportlab.pdfgen import canvas
    
    testar_upload_pdf()