import os
import re
import tempfile
from PIL import Image
import pytesseract
import PyPDF2
from typing import Dict, Optional, List

class ArquivoService:
    def __init__(self):
        # Configurar caminho do tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        self.patterns = {
            'linha_digitavel': [
                r'(\d{5}[\.\s]*\d{5}[\.\s]*\d{5}[\.\s]*\d{6}[\.\s]*\d{5}[\.\s]*\d{6}[\.\s]*\d[\.\s]*\d{14})',
                r'(\d{47,48})',
            ],
            'valor': [
                r'(?:valor|R\$)\s*:?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
                r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            ],
            'banco': [
                r'(banco do brasil|itau|itaú|bradesco|santander|caixa|nubank)',
            ]
        }
    
    def processar_arquivo(self, arquivo_path: str, tipo_arquivo: str) -> Dict:
        """Processa PDF ou imagem e extrai dados"""
        try:
            if tipo_arquivo.lower() == 'pdf':
                texto_extraido = self._extrair_texto_pdf(arquivo_path)
            else:  # imagem
                texto_extraido = self._extrair_texto_imagem(arquivo_path)
            
            dados_extraidos = self._extrair_dados_boleto(texto_extraido)
            
            return {
                'sucesso': True,
                'texto_extraido': texto_extraido,
                'dados_extraidos': dados_extraidos,
                'erro': None
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'texto_extraido': '',
                'dados_extraidos': {},
                'erro': str(e)
            }
    
    def _extrair_texto_pdf(self, pdf_path: str) -> str:
        """Extrai texto de PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                texto = ""
                for page in pdf_reader.pages:
                    texto += page.extract_text() + "\n"
                
                # Se o texto extraído for muito pequeno, pode ser PDF escaneado
                if len(texto.strip()) < 50:
                    raise Exception("PDF parece ser escaneado, seria necessário OCR avançado")
                
                return texto
        except Exception as e:
            raise Exception(f"Erro ao processar PDF: {str(e)}")
    
    def _extrair_texto_imagem(self, imagem_path: str) -> str:
        """OCR em imagem"""
        try:
            # Abrir imagem
            image = Image.open(imagem_path)
            
            # Converter para RGB se necessário
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Aplicar OCR
            texto = pytesseract.image_to_string(image, lang='por')
            
            return texto
        except Exception as e:
            raise Exception(f"Erro no OCR: {str(e)}")
    
    def _extrair_dados_boleto(self, texto: str) -> Dict:
        """Extrai dados estruturados do texto"""
        dados = {}
        texto_limpo = texto.lower().replace('\n', ' ').replace('\r', ' ')
        
        # Extrair linha digitável
        linha = self._extrair_com_patterns(texto, self.patterns['linha_digitavel'])
        if linha:
            dados['linha_digitavel'] = re.sub(r'[^\d]', '', linha)  # Apenas números
            if len(dados['linha_digitavel']) >= 3:
                dados['codigo_banco'] = int(dados['linha_digitavel'][:3])
        
        # Extrair valor
        valor_str = self._extrair_com_patterns(texto, self.patterns['valor'])
        if valor_str:
            dados['valor'] = self._converter_valor(valor_str)
        
        # Extrair banco
        banco = self._extrair_banco(texto_limpo)
        dados['banco'] = banco if banco else 'Banco não identificado'
        
        # Valores padrão
        dados.setdefault('agencia', 1)
        dados.setdefault('codigo_banco', 1)
        dados.setdefault('valor', 0.0)
        
        return dados
    
    def _extrair_com_patterns(self, texto: str, patterns: List[str]) -> Optional[str]:
        """Extrai usando lista de padrões regex"""
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _converter_valor(self, valor_str: str) -> float:
        """Converte string de valor para float"""
        try:
            valor_limpo = re.sub(r'[^\d,.]', '', valor_str)
            valor_limpo = valor_limpo.replace(',', '.')
            return float(valor_limpo)
        except:
            return 0.0
    
    def _extrair_banco(self, texto_limpo: str) -> Optional[str]:
        """Identifica o banco"""
        bancos = {
            'banco do brasil': 'Banco do Brasil',
            'itau': 'Itaú',
            'itaú': 'Itaú', 
            'bradesco': 'Bradesco',
            'santander': 'Santander',
            'caixa': 'Caixa Econômica',
            'nubank': 'NU Pagamentos S.A. – Nubank'
        }
        
        for key, nome in bancos.items():
            if key in texto_limpo:
                return nome
        return None
    
    def validar_dados_extraidos(self, dados: Dict) -> Dict:
        """Valida dados extraídos"""
        erros = []
        warnings = []
        
        if not dados.get('linha_digitavel'):
            erros.append("Linha digitável não encontrada")
        elif len(dados['linha_digitavel']) not in [47, 48]:
            warnings.append("Linha digitável com tamanho suspeito")
        
        if dados.get('valor', 0) <= 0:
            warnings.append("Valor não encontrado ou inválido")
        
        if dados.get('banco') == 'Banco não identificado':
            warnings.append("Banco não identificado")
        
        confianca = 1.0 - (len(erros) * 0.5) - (len(warnings) * 0.2)
        confianca = max(0.0, min(1.0, confianca))
        
        return {
            'valido': len(erros) == 0,
            'erros': erros,
            'warnings': warnings,
            'confianca': confianca
        }