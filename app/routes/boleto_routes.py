from flask import Blueprint, request, jsonify
from app import db
from app.models.boleto import AnaliseBoleto
from app.services.modelo_service import ModeloService
import jwt
import os

boleto_bp = Blueprint('boleto', __name__)
modelo_service = ModeloService()

def get_current_user_optional():
    """Tenta obter o usuário atual se token for fornecido (opcional)"""
    token = None
    if 'Authorization' in request.headers:
        try:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1]
            data = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
            from app.models.user_model import User
            return User.query.get(data['user_id'])
        except:
            return None
    return None

@boleto_bp.route('/analyze', methods=['POST'])
def analisar_boleto():
    """Analisa um boleto (com ou sem usuário logado)"""
    try:
        dados = request.get_json()
        
        # Validar dados de entrada
        campos_obrigatorios = ['banco', 'codigo_banco', 'agencia', 'valor', 'linha_digitavel']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({'erro': f'Campo obrigatório: {campo}'}), 400
        
        print(f"Dados recebidos: {dados}")
        
        # Verificar se há usuário logado (opcional)
        current_user = get_current_user_optional()
        user_id = current_user.id if current_user else None
        print(f"User ID: {user_id}")
        
        # Fazer predição
        resultado_predicao = modelo_service.fazer_predicao(dados)
        print(f"Resultado da predição: {resultado_predicao}")
        
        # Verificar se houve erro na predição
        if 'erro' in resultado_predicao:
            return jsonify({'erro': f'Erro na predição: {resultado_predicao["erro"]}'}), 500
        
        # Extrair features para salvar no banco
        features_extraidas = resultado_predicao.get('features_extraidas', {})
        
        # Salvar no banco de dados
        analise = AnaliseBoleto(
            user_id=user_id,
            banco=modelo_service.mapear_banco(dados['banco']),
            codigo_banco=int(dados['codigo_banco']),
            agencia=int(dados['agencia']),
            valor=float(dados['valor']),
            linha_digitavel=dados['linha_digitavel'],
            linha_cod_banco=features_extraidas.get('linha_cod_banco', 0),
            linha_moeda=features_extraidas.get('linha_moeda', 9),
            linha_valor=features_extraidas.get('linha_valor', 0),
            resultado=resultado_predicao['resultado'],
            probabilidade_falso=resultado_predicao['probabilidade_falso'],
            probabilidade_verdadeiro=resultado_predicao['probabilidade_verdadeiro'],
            confianca=resultado_predicao['confianca']
        )
        
        db.session.add(analise)
        db.session.commit()
        
       # Retornar resultado com explicação SHAP
        resposta = {
            'id': analise.id,
            'user_id': user_id,
            'dados_entrada': dados,
            'resultado': {
                'predicao': resultado_predicao['resultado'],
                'probabilidades': {
                    'falso': resultado_predicao['probabilidade_falso'],
                    'verdadeiro': resultado_predicao['probabilidade_verdadeiro']
                },
                'confianca': resultado_predicao['confianca']
            },
            'features_extraidas': features_extraidas,
            'explicacao': resultado_predicao.get('explicacao_shap', {}), # Adicionado
            'timestamp': analise.created_at.isoformat()
        }
        
        return jsonify(resposta), 200
        
    except Exception as e:
        print(f"Erro na rota analyze: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@boleto_bp.route('/history', methods=['GET'])
def historico_analises():
    """Retorna histórico de análises"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        analises = AnaliseBoleto.query.order_by(AnaliseBoleto.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'analises': [analise.to_dict() for analise in analises.items],
            'total': analises.total,
            'pages': analises.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@boleto_bp.route('/stats', methods=['GET'])
def estatisticas():
    """Retorna estatísticas das análises"""
    try:
        total_analises = AnaliseBoleto.query.count()
        verdadeiros = AnaliseBoleto.query.filter_by(resultado='Verdadeiro').count()
        falsos = AnaliseBoleto.query.filter_by(resultado='Falso').count()
        
        return jsonify({
            'total_analises': total_analises,
            'verdadeiros': verdadeiros,
            'falsos': falsos,
            'porcentagem_verdadeiros': round((verdadeiros / total_analises * 100) if total_analises > 0 else 0, 2),
            'porcentagem_falsos': round((falsos / total_analises * 100) if total_analises > 0 else 0, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
