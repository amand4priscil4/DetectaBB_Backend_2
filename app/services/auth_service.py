# app/services/auth_service.py
import bcrypt
from datetime import datetime, timedelta
import redis

class AuthService:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.failed_attempts = {}
    
    def validate_password_strength(self, password):
        """Política de senhas forte"""
        if len(password) < 8:
            return False, "Senha deve ter pelo menos 8 caracteres"
        if not any(c.isupper() for c in password):
            return False, "Senha deve ter ao menos 1 maiúscula"
        if not any(c.islower() for c in password):
            return False, "Senha deve ter ao menos 1 minúscula"
        if not any(c.isdigit() for c in password):
            return False, "Senha deve ter ao menos 1 número"
        return True, "Senha válida"
    
    def check_brute_force(self, ip_address, email):
        """Proteção contra força bruta"""
        key = f"login_attempts:{ip_address}:{email}"
        attempts = self.redis_client.get(key)
        if attempts and int(attempts) >= 5:
            return False, "Muitas tentativas. Tente em 15 minutos"
        return True, "OK"
    
    def register_failed_attempt(self, ip_address, email):
        """Registra tentativa de login falhada"""
        key = f"login_attempts:{ip_address}:{email}"
        self.redis_client.incr(key)
        self.redis_client.expire(key, 900)  # 15 minutos