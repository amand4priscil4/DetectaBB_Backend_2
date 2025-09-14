from flask import Blueprint, request, jsonify
from app.models.user_model import User
from app import db
from app.services.auth_security_service import AuthSecurityService
from app.middleware.rate_limiter import rate_limiter
import jwt
import datetime
import os
from functools import wraps

auth_bp = Blueprint("auth", __name__)
auth_security = AuthSecurityService()

@auth_bp.route("/register", methods=["POST"])
@rate_limiter.limit(requests_per_minute=5)
def register():
    """Registra um novo usuário com validações de segurança"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ["nome", "email", "senha"]):
            return jsonify({"error": "Campos obrigatórios: nome, email, senha"}), 400
        
        # Validar email
        valid_email, email_msg = auth_security.validate_email_format(data["email"])
        if not valid_email:
            return jsonify({"error": email_msg}), 400
        
        # Validar força da senha
        strong_password, password_msg = auth_security.validate_password_strength(data["senha"])
        if not strong_password:
            return jsonify({"error": password_msg}), 400
        
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email já cadastrado"}), 400
        
        user = User(nome=data["nome"], email=data["email"])
        user.set_password(data["senha"])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "message": "Usuário registrado com sucesso!",
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/login", methods=["POST"])
@rate_limiter.limit(requests_per_minute=20)
def login():
    """Login com proteção contra força bruta"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ["email", "senha"]):
            return jsonify({"error": "Email e senha são obrigatórios"}), 400
        
        client_ip = auth_security.get_client_ip()
        identifier = auth_security.generate_login_identifier(data["email"], client_ip)
        
        can_attempt, brute_msg, attempt_count = auth_security.check_brute_force(identifier)
        if not can_attempt:
            return jsonify({
                "error": f"Muitas tentativas de login. {brute_msg}",
                "retry_after": brute_msg
            }), 429
        
        user = User.query.filter_by(email=data["email"]).first()
        
        if user and user.check_password(data["senha"]) and user.is_active:
            auth_security.register_successful_login(identifier)
            
            token = jwt.encode({
                "user_id": user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, os.getenv("SECRET_KEY"), algorithm="HS256")
            
            response = jsonify({
                "message": "Login realizado com sucesso",
                "token": token,
                "user": user.to_dict()
            })
            
            # Adicionar headers de segurança
            for header, value in auth_security.get_security_headers().items():
                response.headers[header] = value
            
            return response, 200
        else:
            auth_security.register_failed_attempt(identifier)
            return jsonify({
                "error": "Credenciais inválidas",
                "attempts_remaining": max(0, 4 - attempt_count)
            }), 401
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

def token_required(f):
    """Decorador para proteger rotas que precisam de autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Formato de token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token de autenticação necessário'}), 401

        try:
            data = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Usuário não encontrado ou inativo'}), 404
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({'error': f'Erro na validação do token: {str(e)}'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@auth_bp.route("/me", methods=["GET"])
@token_required
@rate_limiter.limit(requests_per_minute=30)
def get_user_data(current_user):
    """Retorna dados do usuário autenticado"""
    return jsonify({
        "user": current_user.to_dict()
    }), 200

@auth_bp.route("/change-password", methods=["PUT"])
@token_required
@rate_limiter.limit(requests_per_minute=3)
def change_password(current_user):
    """Altera a senha do usuário autenticado"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ["senha_atual", "nova_senha"]):
            return jsonify({"error": "Campos obrigatórios: senha_atual, nova_senha"}), 400
        
        # Verificar senha atual
        if not current_user.check_password(data["senha_atual"]):
            return jsonify({"error": "Senha atual incorreta"}), 400
        
        # Validar nova senha
        strong_password, password_msg = auth_security.validate_password_strength(data["nova_senha"])
        if not strong_password:
            return jsonify({"error": password_msg}), 400
        
        if data["senha_atual"] == data["nova_senha"]:
            return jsonify({"error": "A nova senha deve ser diferente da atual"}), 400
        
        # Alterar senha
        current_user.set_password(data["nova_senha"])
        db.session.commit()
        
        return jsonify({"message": "Senha alterada com sucesso!"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/recover-password", methods=["PUT"])
@rate_limiter.limit(requests_per_minute=2)
def recover_password():
    """Recupera senha por email (versão simplificada)"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ["email", "nova_senha"]):
            return jsonify({"error": "Campos obrigatórios: email, nova_senha"}), 400

        # Validar email
        valid_email, email_msg = auth_security.validate_email_format(data["email"])
        if not valid_email:
            return jsonify({"error": email_msg}), 400

        user = User.query.filter_by(email=data["email"]).first()
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404

        # Validar nova senha
        strong_password, password_msg = auth_security.validate_password_strength(data["nova_senha"])
        if not strong_password:
            return jsonify({"error": password_msg}), 400

        if user.check_password(data["nova_senha"]):
            return jsonify({"error": "A nova senha não pode ser igual à senha atual"}), 400

        user.set_password(data["nova_senha"])
        db.session.commit()

        return jsonify({"message": "Senha redefinida com sucesso!"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500