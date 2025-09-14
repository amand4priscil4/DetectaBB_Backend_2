from datetime import datetime, timedelta
from typing import Dict, Tuple

class LimitacaoService:
    def __init__(self):
        self.LIMITE_USUARIO_ANONIMO = 5
        self.LIMITE_USUARIO_LOGADO = 100
        self.usar_redis = False
    
    def verificar_limite_usuario(self, user_id: int = None, ip_address: str = None) -> Tuple[bool, Dict]:
        """Versão simplificada sem Redis"""
        if user_id:
            limite = self.LIMITE_USUARIO_LOGADO
            tipo = 'logado'
        else:
            limite = self.LIMITE_USUARIO_ANONIMO  
            tipo = 'anonimo'
        
        info = {
            'tipo_usuario': tipo,
            'limite_diario': limite,
            'usado_hoje': 0,
            'restante': limite,
            'reset_em': self._proximo_reset()
        }
        
        return True, info
    
    def _proximo_reset(self) -> str:
        amanha = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return amanha.isoformat()
    
    def verificar_qualidade_arquivo(self, tamanho_arquivo: int, tipo_arquivo: str) -> Tuple[bool, str]:
        MAX_SIZE = 10 * 1024 * 1024
        if tamanho_arquivo > MAX_SIZE:
            return False, "Arquivo muito grande"
        return True, "Arquivo válido"
    
    def get_client_ip(self):
        from flask import request
        return request.environ.get('REMOTE_ADDR', '127.0.0.1')
    
    def obter_estatisticas_uso(self, user_id: int = None) -> Dict:
        return {
            'total_analises': 0,
            'historico_7_dias': [],
            'limite_diario': self.LIMITE_USUARIO_LOGADO if user_id else self.LIMITE_USUARIO_ANONIMO
        }