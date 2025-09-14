import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Instância do banco de dados
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configurações do app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///detecta_boletos.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configurar CORS
    CORS(app)
    
    # Inicializar extensões
    db.init_app(app)
    
    # Criar tabelas do banco
    with app.app_context():
        db.create_all()
    
    # Rota simples de teste
    @app.route('/')
    def home():
        return {
            "message": "API Detecta Boletos funcionando!",
            "status": "online"
        }
    
    @app.route('/health')
    def health():
        return {"status": "healthy"}
    
    return app
