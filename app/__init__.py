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
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
    
    CORS(app)
    db.init_app(app)
    
    # Importar modelos
    from app.models.user_model import User
    from app.models.boleto import AnaliseBoleto
    
    # Registrar blueprints
    from app.routes.boleto_routes import boleto_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.upload_routes import upload_bp  # NOVA LINHA
    
    app.register_blueprint(boleto_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')  # NOVA LINHA
    
    with app.app_context():
        db.create_all()
        print("Banco de dados inicializado")
    
    @app.route('/')
    def home():
        return {
            "message": "API Detecta Boletos funcionando!",
            "endpoints": [
                "/api/analyze - POST (dados manuais)",
                "/api/upload/analyze-file - POST (upload arquivo)",  # NOVA LINHA
                "/api/upload/limits - GET (verificar limites)",      # NOVA LINHA
                "/api/history - GET", 
                "/api/stats - GET",
                "/api/auth/register - POST",
                "/api/auth/login - POST",
                "/api/auth/me - GET"
            ]
        }
    
    @app.route('/api/health')
    def health():
        return {"status": "healthy"}
    
    return app