from cryptography.fernet import Fernet
import os
import secrets

class CryptoService:
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY') or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_sensitive_data(self, data):
        """Criptografa dados sensíveis"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Descriptografa dados sensíveis"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def generate_secure_token():
        """Gera token seguro"""
        return secrets.token_urlsafe(32)
