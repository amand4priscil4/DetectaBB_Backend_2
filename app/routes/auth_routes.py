from flask import Blueprint, request, jsonify
from app import db
from app.models.user_model import User
from app.services.auth_security_service import AuthSecurityService
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)
security_service = AuthSecurityService()

# ============ DECORATOR PARA PROTEÇÃO DE ROTAS ============
def token_required(f):
    """Decorator para proteger rotas que precisam de autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar se token foi enviado no header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer TOKEN"
            except IndexError:
                return jsonify({'error': 'Token mal formatado'}), 401
        
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 401
        
        try:
            # Decodificar token
            data = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'Usuário não encontrado'}), 401
            
            if not current_user.is_active:
                return jsonify({'error': 'Usuário desativado'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado. Faça login novamente'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({'error': f'Erro ao validar token: {str(e)}'}), 401
        
        # Passa o usuário para a função protegida
        return f(current_user, *args, **kwargs)
    
    return decorated


# ============ ROTAS PÚBLICAS ============

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registro de novo usuário com validações completas"""
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data:
            return jsonify({'error': 'Nenhum dado fornecido'}), 400
            
        if not data.get('nome'):
            return jsonify({'error': 'Campo obrigatório: nome'}), 400
            
        if not data.get('email'):
            return jsonify({'error': 'Campo obrigatório: email'}), 400
            
        if not data.get('senha'):
            return jsonify({'error': 'Campo obrigatório: senha'}), 400
        
        nome = data['nome'].strip()
        email = data['email'].lower().strip()
        senha = data['senha']
        
        # Validar formato do email
        is_valid, msg = security_service.validate_email_format(email)
        if not is_valid:
            return jsonify({'error': msg}), 400
        
        # Validar força da senha
        is_valid, msg = security_service.validate_password_strength(senha)
        if not is_valid:
            return jsonify({'error': msg}), 400
        
        # Verificar se email já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        # Criar novo usuário
        user = User(nome=nome, email=email)
        user.set_password(senha)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário criado com sucesso',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar usuário: {e}")
        return jsonify({'error': f'Erro ao criar usuário: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login de usuário com proteção contra força bruta"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('senha'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        email = data['email'].lower().strip()
        senha = data['senha']
        
        # Verificar proteção contra força bruta
        client_ip = security_service.get_client_ip()
        identifier = security_service.generate_login_identifier(email, client_ip)
        
        can_attempt, msg, attempts = security_service.check_brute_force(identifier)
        if not can_attempt:
            return jsonify({
                'error': f'Muitas tentativas de login. {msg}',
                'retry_after': msg
            }), 429
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        # Verificar credenciais
        if not user or not user.check_password(senha):
            # Registrar tentativa falhada
            security_service.register_failed_attempt(identifier)
            
            remaining = max(0, 5 - (attempts + 1))
            return jsonify({
                'error': 'Credenciais inválidas',
                'attempts_remaining': remaining
            }), 401
        
        # Verificar se usuário está ativo
        if not user.is_active:
            return jsonify({'error': 'Usuário desativado'}), 403
        
        # Login bem-sucedido - limpar tentativas falhadas
        security_service.register_successful_login(identifier)
        
        # Gerar token JWT (válido por 24 horas)
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, os.getenv('SECRET_KEY', 'dev-secret-key'), algorithm='HS256')
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({'error': f'Erro no login: {str(e)}'}), 500


@auth_bp.route('/users', methods=['GET'])
def listar_usuarios():
    """Lista todos os usuários cadastrados"""
    try:
        usuarios = User.query.all()
        return jsonify({
            'total': len(usuarios),
            'usuarios': [u.to_dict() for u in usuarios]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ ROTAS PROTEGIDAS ============

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Retorna dados do usuário logado"""
    return jsonify({
        'user': current_user.to_dict()
    }), 200


@auth_bp.route('/update', methods=['PUT'])
@token_required
def update_user(current_user):
    """Atualiza dados do usuário"""
    try:
        data = request.get_json()
        
        if data.get('nome'):
            current_user.nome = data['nome'].strip()
        
        if data.get('email'):
            email = data['email'].lower().strip()
            
            # Validar formato
            is_valid, msg = security_service.validate_email_format(email)
            if not is_valid:
                return jsonify({'error': msg}), 400
            
            # Verificar se já existe outro usuário com esse email
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != current_user.id:
                return jsonify({'error': 'Email já cadastrado por outro usuário'}), 400
            
            current_user.email = email
        
        if data.get('senha'):
            # Validar nova senha
            is_valid, msg = security_service.validate_password_strength(data['senha'])
            if not is_valid:
                return jsonify({'error': msg}), 400
            
            current_user.set_password(data['senha'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário atualizado com sucesso',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar usuário: {str(e)}'}), 500


# ============ ROTAS DE TESTE ============

@auth_bp.route('/test', methods=['GET'])
def test():
    """Rota de teste simples"""
    return jsonify({
        'message': 'Auth blueprint funcionando!',
        'endpoints': {
            'public': [
                'POST /api/auth/register',
                'POST /api/auth/login',
                'GET /api/auth/users',
                'GET /api/auth/test'
            ],
            'protected': [
                'GET /api/auth/me (requer token)',
                'PUT /api/auth/update (requer token)'
            ]
        }
    }), 200