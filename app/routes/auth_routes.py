from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    """Teste básico de registro"""
    try:
        data = request.get_json()
        return jsonify({
            "success": True,
            "message": "Endpoint funcionando!",
            "data_received": data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/test", methods=["GET"])
def test():
    """Rota de teste simples"""
    return jsonify({"message": "Auth blueprint funcionando!"}), 200
