from flask import Blueprint, jsonify, request

test_bp = Blueprint('test', __name__)

@test_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        "message": "Blueprint funcionando!",
        "blueprint": "test_bp",
        "status": "success"
    }), 200

@test_bp.route('/auth/test', methods=['GET'])
def auth_test():
    return jsonify({
        "message": "Rota auth/test funcionando!",
        "endpoint": "/api/auth/test"
    }), 200

@test_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        return jsonify({
            "success": True,
            "message": "Endpoint de registro funcionando!",
            "data_received": data
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
