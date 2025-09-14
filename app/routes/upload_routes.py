import os
import tempfile
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app import db
from app.models.boleto import AnaliseBoleto
from app.services.arquivo_service import ArquivoService
from app.services.modelo_service import ModeloService
from app.services.limitacao_service import LimitacaoService
from app.routes.auth_routes import token_required
from app.middleware.rate_limiter import rate_limiter
import jwt

upload_bp = Blueprint('upload', __name__)

# Instanciar serviços
arquivo_service = ArquivoService()
modelo_service = ModeloService()
limitacao_service = LimitacaoService()

# Configurações de upload
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user_optional():
    """Tenta obter o usuário atual se token for fornecido"""
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

@upload_bp.route('/analyze-file', methods=['POST'])
@rate_limiter.limit(requests_per_minute=10)
def analisar_arquivo():
    """Analisa boleto a partir de arquivo PDF ou imagem"""
    try:
        # Verificar se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400
        
        # Verificar extensão
        if not allowed_file(file.filename):
            return jsonify({
                'erro': f'Tipo de arquivo não permitido. Permitidos: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Obter usuário atual (se logado)
        current_user = get_current_user_optional()
        user_id = current_user.id if current_user else None
        client_ip = limitacao_service.get_client_ip()
        
        # Verificar limites de uso
        pode_analisar, info_limite = limitacao_service.verificar_limite_usuario(user_id, client_ip)
        if not pode_analisar:
            return jsonify({
                'erro': 'Limite de análises diárias excedido',
                'limite_info': info_limite,
                'sugestao': 'Faça login para ter acesso ao limite estendido' if not user_id else 'Tente novamente amanhã'
            }), 429
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_boleto_{os.getpid()}_{filename}")
        
        file.save(temp_path)
        
        try:
            # Verificar tamanho do arquivo
            file_size = os.path.getsize(temp_path)
            valido, msg = limitacao_service.verificar_qualidade_arquivo(file_size, file_extension)
            if not valido:
                return jsonify({'erro': msg}), 400
            
            # Processar arquivo
            resultado_processamento = arquivo_service.processar_arquivo(temp_path, file_extension)
            
            if not resultado_processamento['sucesso']:
                return jsonify({
                    'erro': f'Erro ao processar arquivo: {resultado_processamento["erro"]}'
                }), 500
            
            # Validar dados extraídos
            dados_extraidos = resultado_processamento['dados_extraidos']
            validacao = arquivo_service.validar_dados_extraidos(dados_extraidos)
            
            if not validacao['valido']:
                return jsonify({
                    'erro': 'Não foi possível extrair dados válidos do boleto',
                    'detalhes': validacao['erros'],
                    'texto_extraido': resultado_processamento['texto_extraido'][:500] + '...' if len(resultado_processamento['texto_extraido']) > 500 else resultado_processamento['texto_extraido']
                }), 400
            
            # Fazer predição com o modelo ML
            try:
                predicao = modelo_service.fazer_predicao(dados_extraidos)
                
                if 'erro' in predicao:
                    return jsonify({
                        'erro': f'Erro na análise ML: {predicao["erro"]}',
                        'dados_extraidos': dados_extraidos,
                        'validacao': validacao
                    }), 500
                
            except Exception as e:
                return jsonify({
                    'erro': f'Erro na predição: {str(e)}',
                    'dados_extraidos': dados_extraidos
                }), 500
            
            # Salvar análise no banco
            features_extraidas = predicao.get('features_extraidas', {})
            
            analise = AnaliseBoleto(
                user_id=user_id,
                banco=modelo_service.mapear_banco(dados_extraidos['banco']),
                codigo_banco=dados_extraidos.get('codigo_banco', 1),
                agencia=dados_extraidos.get('agencia', 1),
                valor=dados_extraidos.get('valor', 0.0),
                linha_digitavel=dados_extraidos.get('linha_digitavel', ''),
                linha_cod_banco=features_extraidas.get('linha_cod_banco', 0),
                linha_moeda=features_extraidas.get('linha_moeda', 9),
                linha_valor=features_extraidas.get('linha_valor', 0),
                resultado=predicao['resultado'],
                probabilidade_falso=predicao['probabilidade_falso'],
                probabilidade_verdadeiro=predicao['probabilidade_verdadeiro'],
                confianca=predicao['confianca']
            )
            
            db.session.add(analise)
            db.session.commit()
            
            # Resposta completa
            resposta = {
                'id': analise.id,
                'user_id': user_id,
                'arquivo_processado': {
                    'nome_arquivo': filename,
                    'tipo': file_extension,
                    'tamanho_kb': round(file_size / 1024, 2),
                    'confianca_extracao': validacao['confianca']
                },
                'dados_extraidos': dados_extraidos,
                'validacao': validacao,
                'resultado_ml': {
                    'predicao': predicao['resultado'],
                    'probabilidades': {
                        'falso': predicao['probabilidade_falso'],
                        'verdadeiro': predicao['probabilidade_verdadeiro']
                    },
                    'confianca': predicao['confianca']
                },
                'limite_info': info_limite,
                'timestamp': analise.created_at.isoformat()
            }
            
            # Incluir texto extraído para usuários logados (para debug)
            if user_id:
                resposta['debug'] = {
                    'texto_extraido': resultado_processamento['texto_extraido'][:1000] + '...' if len(resultado_processamento['texto_extraido']) > 1000 else resultado_processamento['texto_extraido']
                }
            
            return jsonify(resposta), 200
            
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@upload_bp.route('/limits', methods=['GET'])
@rate_limiter.limit(requests_per_minute=30)
def obter_limites():
    """Retorna informações sobre limites de uso"""
    current_user = get_current_user_optional()
    user_id = current_user.id if current_user else None
    client_ip = limitacao_service.get_client_ip()
    
    pode_analisar, info_limite = limitacao_service.verificar_limite_usuario(user_id, client_ip)
    estatisticas = limitacao_service.obter_estatisticas_uso(user_id)
    
    return jsonify({
        'pode_analisar': pode_analisar,
        'limite_atual': info_limite,
        'estatisticas': estatisticas,
        'formatos_suportados': list(ALLOWED_EXTENSIONS),
        'tamanho_maximo_mb': MAX_FILE_SIZE / (1024 * 1024)
    }), 200

@upload_bp.route('/test-ocr', methods=['POST'])
@token_required
@rate_limiter.limit(requests_per_minute=5)
def testar_ocr(current_user):
    """Endpoint para testar OCR sem fazer análise (apenas usuários logados)"""
    try:
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'erro': 'Tipo de arquivo não permitido'}), 400
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        temp_path = os.path.join(UPLOAD_FOLDER, f"test_ocr_{os.getpid()}_{filename}")
        
        file.save(temp_path)
        
        try:
            # Processar apenas para extração de texto
            resultado = arquivo_service.processar_arquivo(temp_path, file_extension)
            
            return jsonify({
                'sucesso': resultado['sucesso'],
                'texto_extraido': resultado['texto_extraido'],
                'dados_extraidos': resultado['dados_extraidos'],
                'erro': resultado['erro']
            }), 200
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({'erro': f'Erro no teste OCR: {str(e)}'}), 500