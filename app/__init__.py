from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///detecta_boletos.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS - aceita tudo temporariamente
    CORS(app)
    
    # Handler para OPTIONS (preflight)
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    db.init_app(app)
    
    @app.route('/')
    def home():
        return {"message": "API Detecta Boletos funcionando!", "status": "online"}
    
    @app.route('/health')
    def health():
        return {"status": "healthy"}
    
    # Registrar blueprints
    try:
        from app.routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        print("✅ Auth blueprint registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar auth blueprint: {e}")
    
    try:
        from app.routes.boleto_routes import boleto_bp
        app.register_blueprint(boleto_bp, url_prefix='/api')
        print("✅ Boleto blueprint registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar boleto blueprint: {e}")
    
    try:
        from app.routes.test_routes import test_bp
        app.register_blueprint(test_bp, url_prefix='/api')
        print("✅ Test blueprint registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar test blueprint: {e}")
    
    return app