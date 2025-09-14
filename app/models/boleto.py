from app import db
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON

class AnaliseBoleto(db.Model):
    __tablename__ = 'analises_boleto'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NOVA LINHA
    
    # Dados de entrada
    banco = db.Column(db.Float, nullable=False)
    codigo_banco = db.Column(db.Integer, nullable=False)
    agencia = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    linha_digitavel = db.Column(db.String(50), nullable=False)
    
    # Features extraídas
    linha_cod_banco = db.Column(db.Integer, nullable=False)
    linha_moeda = db.Column(db.Integer, nullable=False)
    linha_valor = db.Column(db.Integer, nullable=False)
    
    # Resultado
    resultado = db.Column(db.String(20), nullable=False)
    probabilidade_falso = db.Column(db.Float, nullable=False)
    probabilidade_verdadeiro = db.Column(db.Float, nullable=False)
    confianca = db.Column(db.Float, nullable=False)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,  # NOVA LINHA
            'dados_entrada': {
                'banco': self.banco,
                'codigo_banco': self.codigo_banco,
                'agencia': self.agencia,
                'valor': self.valor,
                'linha_digitavel': self.linha_digitavel
            },
            'resultado': {
                'predicao': self.resultado,
                'probabilidades': {
                    'falso': self.probabilidade_falso,
                    'verdadeiro': self.probabilidade_verdadeiro
                },
                'confianca': self.confianca
            },
            'created_at': self.created_at.isoformat()
        }