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
    
    CORS(app, 
         resources={r"/*": {
             "origins": ["http://localhost:8100", "http://localhost:3000"],
             "allow_headers": ["Content-Type", "Authorization"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
         }})
    
    db.init_app(app)
    
    @app.route('/')
    def home():
        return {"message": "API Detecta Boletos funcionando!", "status": "online"}
    
    @app.route('/health')
    def health():
        return {"status": "healthy"}
    
    # Registrar auth blueprint - ADICIONE ISTO
    try:
        from app.routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        print("✅ Auth blueprint registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar auth blueprint: {e}")
    
    # Registrar test blueprint (pode manter ou remover)
    try:
        from app.routes.test_routes import test_bp
        app.register_blueprint(test_bp, url_prefix='/api')
        print("✅ Test blueprint registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar test blueprint: {e}")
    
    return app
