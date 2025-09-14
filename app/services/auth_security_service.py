import bcrypt
import re
from datetime import datetime, timedelta
from typing import Tuple, Dict
from flask import request

class AuthSecurityService:
    def __init__(self):
        # Cache simples para tentativas de login (usar Redis em produção)
        self.failed_attempts = {}
        self.blocked_ips = {}
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Valida força da senha"""
        if len(password) < 8:
            return False, "Senha deve ter pelo menos 8 caracteres"
        
        if len(password) > 128:
            return False, "Senha muito longa (máximo 128 caracteres)"
        
        if not re.search(r'[A-Z]', password):
            return False, "Senha deve conter ao menos uma letra maiúscula"
        
        if not re.search(r'[a-z]', password):
            return False, "Senha deve conter ao menos uma letra minúscula"
        
        if not re.search(r'\d', password):
            return False, "Senha deve conter ao menos um número"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Senha deve conter ao menos um caractere especial"
        
        # Verificar senhas comuns
        common_passwords = ['12345678', 'password', 'admin123', 'qwerty123']
        if password.lower() in common_passwords:
            return False, "Senha muito comum, escolha uma mais segura"
        
        return True, "Senha forte"
    
    def check_brute_force(self, identifier: str) -> Tuple[bool, str, int]:
        """Verifica tentativas de força bruta"""
        now = datetime.now()
        
        # Limpar tentativas antigas (mais de 15 minutos)
        self._cleanup_old_attempts(now)
        
        if identifier not in self.failed_attempts:
            return True, "OK", 0
        
        attempts = self.failed_attempts[identifier]
        attempt_count = len(attempts)
        
        # Verificar se está bloqueado
        if attempt_count >= 5:
            last_attempt = max(attempts)
            time_diff = (now - last_attempt).total_seconds()
            
            if time_diff < 900:  # 15 minutos
                remaining = 900 - int(time_diff)
                return False, f"Bloqueado por {remaining//60}m {remaining%60}s", attempt_count
            else:
                # Resetar após 15 minutos
                del self.failed_attempts[identifier]
                return True, "OK", 0
        
        return True, "OK", attempt_count
    
    def register_failed_attempt(self, identifier: str):
        """Registra tentativa falhada"""
        now = datetime.now()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(now)
        
        # Manter apenas as últimas 10 tentativas
        if len(self.failed_attempts[identifier]) > 10:
            self.failed_attempts[identifier] = self.failed_attempts[identifier][-10:]
    
    def register_successful_login(self, identifier: str):
        """Limpa tentativas após login bem-sucedido"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def _cleanup_old_attempts(self, now: datetime):
        """Remove tentativas antigas"""
        cutoff = now - timedelta(minutes=15)
        
        for identifier in list(self.failed_attempts.keys()):
            # Filtrar tentativas recentes
            recent_attempts = [
                attempt for attempt in self.failed_attempts[identifier]
                if attempt > cutoff
            ]
            
            if recent_attempts:
                self.failed_attempts[identifier] = recent_attempts
            else:
                del self.failed_attempts[identifier]
    
    def get_client_ip(self) -> str:
        """Obtém IP real do cliente"""
        # Verificar se está atrás de proxy/load balancer
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or '127.0.0.1'
    
    def generate_login_identifier(self, email: str, ip: str) -> str:
        """Gera identificador único para controle de força bruta"""
        return f"{ip}:{email}"
    
    def validate_email_format(self, email: str) -> Tuple[bool, str]:
        """Valida formato básico do email"""
        if not email or len(email) > 254:
            return False, "Email inválido"
        
        # Regex básico para email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Formato de email inválido"
        
        return True, "Email válido"
    
    def get_security_headers(self) -> Dict[str, str]:
        """Retorna headers de segurança"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        }