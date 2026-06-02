from functools import wraps
from flask import request, jsonify

# Dicionário de sessão para este nível 1
_tokens_ativos = {}

def requer_autenticacao(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"erro": "Token não fornecido ou inválido"}), 401
        token = auth_header.split(" ")[1]

        usuario_info = _tokens_ativos.get(token)
        if not usuario_info:
            return jsonify({"erro": "Token expirado ou inválido"}), 401

        request.usuario_logado = usuario_info
        request.token_logado = token
        return f(*args, **kwargs)
    return decorado

def verificar_permissao_hierarquica(f):
    """
    Injeta o escopo de query dependendo do perfil:
    admin/diretoria: 'global'
    coordenador: 'curso'
    professor: 'disciplina_aluno'
    visualizador: 'somente_leitura_anonimizada'
    """
    @wraps(f)
    def decorado(*args, **kwargs):
        perfil = request.usuario_logado.get("perfil")
        if perfil == "admin":
            request.escopo_dados = "global"
        elif perfil == "coordenador":
            request.escopo_dados = "curso"
        elif perfil in ["professor", "visualizador"]:
            request.escopo_dados = "restrito"
        else:
            return jsonify({"erro": "Acesso negado."}), 403

        return f(*args, **kwargs)
    return decorado
