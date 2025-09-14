import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Tuple

class SecurityService:
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def validate_file_security(self, file_path: str) -> Tuple[bool, str]:
        """Validação básica de segurança de arquivos"""
        try:
            # Verificar se arquivo existe
            if not os.path.exists(file_path):
                return False, "Arquivo não encontrado"
            
            # Verificar extensão
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.ALLOWED_EXTENSIONS:
                return False, f"Extensão não permitida: {file_ext}"
            
            # Verificar tamanho
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                return False, f"Arquivo muito grande: {file_size/1024/1024:.1f}MB"
            
            # Verificar se não é arquivo vazio
            if file_size == 0:
                return False, "Arquivo vazio"
            
            # Verificação básica de header por extensão
            if not self._validate_file_header(file_path, file_ext):
                return False, "Header do arquivo suspeito"
            
            return True, "Arquivo válido"
            
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"
    
    def _validate_file_header(self, file_path: str, extension: str) -> bool:
        """Valida header básico do arquivo"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(10)
            
            # Headers conhecidos
            headers = {
                '.pdf': [b'%PDF'],
                '.jpg': [b'\xff\xd8\xff'],
                '.jpeg': [b'\xff\xd8\xff'],
                '.png': [b'\x89PNG'],
                '.tiff': [b'II*\x00', b'MM\x00*'],
                '.bmp': [b'BM']
            }
            
            expected_headers = headers.get(extension, [])
            return any(header.startswith(h) for h in expected_headers)
            
        except:
            return False
    
    def generate_secure_filename(self, original_filename: str) -> str:
        """Gera nome seguro para arquivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(original_filename.encode()).hexdigest()[:8]
        ext = Path(original_filename).suffix.lower()
        return f"upload_{timestamp}_{file_hash}{ext}"
    
    def sanitize_filename(self, filename: str) -> str:
        """Remove caracteres perigosos do nome do arquivo"""
        # Remover caracteres perigosos
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        clean_name = filename
        for char in dangerous_chars:
            clean_name = clean_name.replace(char, '_')
        
        # Limitar tamanho
        if len(clean_name) > 255:
            name, ext = os.path.splitext(clean_name)
            clean_name = name[:250] + ext
        
        return clean_name