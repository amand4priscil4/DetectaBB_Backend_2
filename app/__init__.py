import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///detecta_boletos.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS mais específico
    CORS(app, 
         resources={r"/*": {
             "origins": ["http://localhost:8100", "http://localhost:3000"],
             "allow_headers": ["Content-Type", "Authorization"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
         }})
    
    db.init_app(app)
    
    @app.route('/')
    def home():
        return {
            "message": "API Detecta Boletos funcionando!",
            "status": "online"
        }
    
    @app.route('/health')
    def health():
        return {"status": "healthy"}
    
    # Registrar blueprint simples para teste
    try:
        from app.routes.test_routes import test_bp
        app.register_blueprint(test_bp, url_prefix='/api')
        print("✅ Blueprint de teste registrado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar blueprint: {e}")
    except Exception as e:
        print(f"❌ Erro geral ao registrar blueprint: {e}")
    
    return app
