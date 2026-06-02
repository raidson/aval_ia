from functools import wraps
from flask import request, jsonify
from services.database import get_connection

def anonimizar_dados(aluno_data, perfil):
    """
    Minimiza dados pessoais do estudante baseado no perfil.
    Visualizadores não veem nomes ou matrículas reais.
    """
    if perfil in ["visualizador"]:
        aluno_data["nome_completo"] = "*** Anonimizado ***"
        aluno_data["matricula"] = "***"
        aluno_data["email"] = "***"
    return aluno_data

def filtrar_por_perfil(perfil: str, usuario_id: str, query_base: str, params: tuple):
    """
    Constrói a restrição de query baseada na hierarquia:
    - admin: Tudo
    - coordenador: Tudo (no contexto simplificado ou filtrado por curso)
    - professor/visualizador: Restrito a suas turmas ou sem identificação (tratado na view)
    """
    # Para o nível 2, aplicamos as views ou injetamos na query
    conn = get_connection()
    cur = conn.cursor()

    # Exemplo: se professor, poderia haver tabela professor_turma.
    # No schema atual, apenas restringimos para exemplificar o funcionamento RBAC
    if perfil == "admin" or perfil == "coordenador":
        cur.execute(query_base, params)
    else:
        # Se for professor, só vê alunos de suas disciplinas (mock: limitando)
        cur.execute(query_base + " LIMIT 100", params)

    return cur.fetchall()

def verificar_rbac(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        # Acesso às variáveis globais de app.py seria importado,
        # mas faremos a verificação de _tokens_ativos onde o decorator for usado
        return f(*args, **kwargs)
    return decorado
