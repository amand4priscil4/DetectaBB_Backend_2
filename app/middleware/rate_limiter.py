import time
from functools import wraps
from flask import request, jsonify
from collections import defaultdict, deque

class SimpleRateLimiter:
    def __init__(self):
        # Armazenar requisições por IP e endpoint
        self.requests = defaultdict(lambda: defaultdict(deque))
        self.cleanup_interval = 300  # Limpar a cada 5 minutos
        self.last_cleanup = time.time()
    
    def limit(self, requests_per_minute=60, per_endpoint=True):
        """
        Decorator para rate limiting
        requests_per_minute: número máximo de requests por minuto
        per_endpoint: se True, limite por endpoint; se False, limite global
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                current_time = time.time()
                client_ip = self._get_client_ip()
                
                # Determinar chave do rate limit
                if per_endpoint:
                    key = f"{request.endpoint}"
                else:
                    key = "global"
                
                # Cleanup periódico
                if current_time - self.last_cleanup > self.cleanup_interval:
                    self._cleanup_old_requests(current_time)
                    self.last_cleanup = current_time
                
                # Obter fila de requests deste IP para este endpoint
                request_times = self.requests[client_ip][key]
                
                # Remover requests antigas (> 1 minuto)
                while request_times and current_time - request_times[0] > 60:
                    request_times.popleft()
                
                # Verificar se excedeu o limite
                if len(request_times) >= requests_per_minute:
                    return jsonify({
                        'error': 'Rate limit excedido',
                        'detail': f'Máximo {requests_per_minute} requests por minuto',
                        'retry_after': 60 - (current_time - request_times[0])
                    }), 429
                
                # Registrar esta requisição
                request_times.append(current_time)
                
                # Executar função original
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    def _get_client_ip(self):
        """Obtém IP do cliente"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.remote_addr or '127.0.0.1'
    
    def _cleanup_old_requests(self, current_time):
        """Remove dados antigos para liberar memória"""
        cutoff = current_time - 3600  # Manter apenas última hora
        
        for ip in list(self.requests.keys()):
            for endpoint in list(self.requests[ip].keys()):
                request_times = self.requests[ip][endpoint]
                
                # Remover requests antigas
                while request_times and request_times[0] < cutoff:
                    request_times.popleft()
                
                # Remover endpoints vazios
                if not request_times:
                    del self.requests[ip][endpoint]
            
            # Remover IPs vazios
            if not self.requests[ip]:
                del self.requests[ip]

# Instância global do rate limiter
rate_limiter = SimpleRateLimiter()