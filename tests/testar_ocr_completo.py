import pytesseract
from PIL import Image

try:
    # Configurar caminho
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Testar versão
    print("Versão do Tesseract:", pytesseract.get_tesseract_version())
    
    # Testar OCR simples
    print("OCR configurado e funcionando!")
    
except Exception as e:
    print(f"Erro: {e}")