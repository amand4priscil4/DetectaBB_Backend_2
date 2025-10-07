import os
import re
import tempfile
from PIL import Image
import pytesseract
import PyPDF2
from typing import Dict, Optional, List
from pdf2image import convert_from_path # <-- MUDANÇA AQUI: Novo import

class ArquivoService:
    def __init__(self):
        # <-- MUDANÇA AQUI: A linha que definia o caminho do Tesseract foi REMOVIDA
        
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
            if 'pdf' in tipo_arquivo.lower(): # <-- MUDANÇA AQUI: Lógica mais flexível para 'application/pdf'
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
    
    # <-- MUDANÇA AQUI: Função de PDF totalmente substituída
    def _extrair_texto_pdf(self, pdf_path: str) -> str:
        """Extrai texto de PDF, usando OCR se necessário para PDFs escaneados."""
        texto_final = ""
        try:
            # 1. Tenta extrair texto diretamente com PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    texto_final += page.extract_text() + "\n"
            
            # 2. Se o texto for muito curto, aciona o OCR com Tesseract
            if len(texto_final.strip()) < 100:
                texto_ocr = ""
                # Converte o PDF em uma lista de imagens
                imagens_pdf = convert_from_path(pdf_path)
                for imagem in imagens_pdf:
                    # Aplica o OCR em cada página/imagem
                    texto_ocr += pytesseract.image_to_string(imagem, lang='por') + "\n"
                texto_final = texto_ocr

            if not texto_final.strip():
                 raise Exception("Não foi possível extrair texto do PDF, mesmo com OCR.")

            return texto_final
        except Exception as e:
            raise Exception(f"Erro ao processar PDF: {str(e)}")

    def _extrair_texto_imagem(self, imagem_path: str) -> str:
        """OCR em imagem"""
        try:
            image = Image.open(imagem_path)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            texto = pytesseract.image_to_string(image, lang='por')
            
            return texto
        except Exception as e:
            raise Exception(f"Erro no OCR: {str(e)}")
    
    def _extrair_dados_boleto(self, texto: str) -> Dict:
        """Extrai dados estruturados do texto"""
        dados = {}
        texto_limpo = texto.lower().replace('\n', ' ').replace('\r', ' ')
        
        linha = self._extrair_com_patterns(texto, self.patterns['linha_digitavel'])
        if linha:
            dados['linha_digitavel'] = re.sub(r'[^\d]', '', linha)
            if len(dados['linha_digitavel']) >= 3:
                dados['codigo_banco'] = int(dados['linha_digitavel'][:3])
        
        valor_str = self._extrair_com_patterns(texto, self.patterns['valor'])
        if valor_str:
            dados['valor'] = self._converter_valor(valor_str)
        
        banco = self._extrair_banco(texto_limpo)
        dados['banco'] = banco if banco else 'Banco não identificado'
        
        dados.setdefault('agencia', 1)
        dados.setdefault('codigo_banco', 1)
        dados.setdefault('valor', 0.0)
        
        return dados
    
    def _extrair_com_patterns(self, texto: str, patterns: List[str]) -> Optional[str]:
        """Extrai usando lista de padrões regex"""
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                # Se o padrão tiver grupos de captura, retorna o primeiro, senão, o match completo
                return match.group(1) if match.groups() else match.group(0)
        return None
    
    def _converter_valor(self, valor_str: str) -> float:
        """Converte string de valor para float"""
        try:
            # Remove tudo que não for dígito, vírgula ou ponto
            valor_limpo = re.sub(r'[^\d,.]', '', valor_str)
            # Lida com casos como '1.234,56'
            if '.' in valor_limpo and ',' in valor_limpo:
                valor_limpo = valor_limpo.replace('.', '')
            valor_limpo = valor_limpo.replace(',', '.')
            return float(valor_limpo)
        except:
            return 0.0
    
    def _extrair_banco(self, texto_limpo: str) -> Optional[str]:
        """Identifica o banco"""
        bancos = {
            'banco do brasil': 'Banco do Brasil',
            'itau': 'Itaú', 'itaú': 'Itaú', 
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
            warnings.append(f"Linha digitável com tamanho suspeito: {len(dados['linha_digitavel'])} dígitos")
        
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