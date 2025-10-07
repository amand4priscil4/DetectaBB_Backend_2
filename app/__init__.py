from flask import Flask
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
    
    # ✅ CORS SIMPLES - uma linha só
    CORS(app)
    
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
        from app.routes.upload_routes import upload_bp
        app.register_blueprint(upload_bp, url_prefix='/api/upload')
        print("✅ Upload blueprint registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar upload blueprint: {e}")

        # ⚠️ ENDPOINT TEMPORÁRIO - REMOVER DEPOIS!
    @app.route('/secret-reset-db-12345', methods=['POST'])
    def reset_database():
        """CUIDADO: Apaga e recria o banco!"""
        try:
            db.drop_all()
            db.create_all()
            return {"message": "✅ Banco resetado com sucesso!"}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    return app