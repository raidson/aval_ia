"""
Módulo: api/app.py
API REST do Nexus construída com Flask, utilizando o padrão Application Factory.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
import io
import hashlib
import secrets
import uuid
from functools import wraps
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import re
import urllib.parse
import pandas as pd
import json
import statistics

from services.database import init_db, get_connection, close_connection
from services.repositorio_sqlite import RepositorioSQLite
from services.aluno_service import AlunoService
from services.indicador_service import IndicadorService
from services.lyceum_service import LyceumService
from models.usuario import Usuario, PerfilUsuario
from models.aluno import Aluno
from services.bokeh_service import BokehService
from api.rbac import anonimizar_dados

# Tokens de sessão ativos {token: usuario_id} - Mantido globalmente, gerenciado pela app.
_tokens_ativos: dict = {}

def create_app():
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__)

    with app.app_context():
        init_db()

    @app.teardown_appcontext
    def teardown_db(exception):
        close_connection(exception)

    # --- Serviços e Repositórios (inicializados aqui para ter acesso ao contexto) ---
    repo_alunos = RepositorioSQLite("alunos")
    repo_turmas = RepositorioSQLite("disciplinas")
    repo_indicadores = RepositorioSQLite("indicadores")
    repo_usuarios = RepositorioSQLite("usuarios")
    repo_auditoria = RepositorioSQLite("auditoria")

    aluno_service = AlunoService(repo_alunos)
    indicador_service = IndicadorService(repo_indicadores)
    lyceum_service = LyceumService()

    # ------------------------------------------------------------------ #
    # Decorators de Autenticação e Permissão
    # ------------------------------------------------------------------ #
    def requer_autenticacao(f):
        @wraps(f)
        def decorado(*args, **kwargs):
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if token not in _tokens_ativos:
                return jsonify({"erro": "Não autorizado. Token inválido ou ausente."}), 401
            return f(*args, **kwargs)
        return decorado

    def requer_permissao(acao: str):
        def decorator(f):
            @wraps(f)
            def decorado(*args, **kwargs):
                token = request.headers.get("Authorization", "").replace("Bearer ", "")
                usuario_id = _tokens_ativos.get(token)
                dados_usuario = repo_usuarios.buscar(usuario_id)
                if not dados_usuario:
                    return jsonify({"erro": "Usuário não encontrado."}), 403
                perfil = PerfilUsuario(dados_usuario["perfil"])
                usuario = Usuario(id=dados_usuario["id"], nome=dados_usuario["nome"], matricula=dados_usuario.get("matricula", ""), perfil=perfil)
                if not usuario.tem_permissao(acao):
                    return jsonify({"erro": f"Permissão negada para ação: {acao}"}), 403
                return f(*args, **kwargs)
            return decorado
        return decorator

    def registrar_auditoria(acao: str, token: str, detalhes: dict = {}):
        from datetime import datetime
        usuario_id = _tokens_ativos.get(token, "desconhecido")
        entrada_id = str(uuid.uuid4())
        repo_auditoria.salvar(entrada_id, {
            "id": entrada_id, "usuario_id": usuario_id, "acao": acao,
            "detalhe": detalhes, "timestamp": datetime.now().isoformat(),
        })

    # ------------------------------------------------------------------ #
    # Rotas de Interface e Autenticação
    # ------------------------------------------------------------------ #
    @app.route("/login", methods=["GET"])
    def login_page():
        return render_template("login.html")

    @app.route("/dashboard", methods=["GET"])
    def dashboard_page():
        return render_template("dashboard.html")

    @app.route("/cadastro", methods=["GET"])
    def cadastro_page():
        return render_template("cadastro.html")

    @app.route("/auth/login", methods=["POST"])
    def login():
        dados = request.get_json()
        if not dados or "matricula" not in dados or "senha" not in dados:
            return jsonify({"erro": "Matrícula e senha são obrigatórios."}), 400
        resultado = repo_usuarios.filtrar("matricula", dados["matricula"])
        if not resultado:
            return jsonify({"erro": "Credenciais inválidas."}), 401
        dados_usuario = resultado[0]
        senha_hash = hashlib.sha256(dados["senha"].encode()).hexdigest()
        if dados_usuario.get("senha_hash") != senha_hash:
            return jsonify({"erro": "Credenciais inválidas."}), 401
        token = secrets.token_hex(32)
        _tokens_ativos[token] = dados_usuario["id"]
        return jsonify({"token": token, "perfil": dados_usuario["perfil"], "nome": dados_usuario["nome"]}), 200

    # ... (outras rotas de autenticação como /auth/registrar e /auth/logout)

    # ------------------------------------------------------------------ #
    # Rotas da API (/alunos, /turmas, etc.)
    # ------------------------------------------------------------------ #
    @app.route("/turmas", methods=["GET"])
    @requer_autenticacao
    def listar_turmas():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT turma FROM registros_academicos WHERE turma IS NOT NULL AND turma != ''")
            turmas_raw = [r[0] for r in cursor.fetchall()]
            turmas = []
            for t_code in turmas_raw:
                cursor.execute("""
                    SELECT ra.aluno_id, ra.media_final, ra.situacao, ra.risco_academico, a.curso, ra.serie
                    FROM registros_academicos ra JOIN alunos a ON ra.aluno_id = a.id WHERE ra.turma = ?
                """, (t_code,))
                rows = cursor.fetchall()
                if not rows: continue
                
                student_records = {r[0]: {"medias": [], "situacoes": [], "riscos": [], "cursos": [], "series": []} for r in rows}
                for r in rows:
                    if r[1] is not None: student_records[r[0]]["medias"].append(r[1])
                    if r[2]: student_records[r[0]]["situacoes"].append(r[2])
                    if r[3]: student_records[r[0]]["riscos"].append(r[3])
                    if r[4]: student_records[r[0]]["cursos"].append(r[4])
                    if r[5] is not None: student_records[r[0]]["series"].append(r[5])

                all_medias = [m for s in student_records.values() for m in s["medias"]]
                avg_media = sum(all_medias) / len(all_medias) if all_medias else 0.0
                
                cursor.execute("SELECT a.frequencias, ra.serie FROM registros_academicos ra JOIN alunos a ON ra.aluno_id = a.id WHERE ra.turma = ?", (t_code,))
                all_freqs = []
                for f_row in cursor.fetchall():
                    try:
                        freqs_list = json.loads(f_row[0]) if f_row[0] else []
                        for f in freqs_list:
                            if f.get("periodo") == f_row[1] and "percentual" in f: all_freqs.append(f["percentual"])
                    except: pass
                avg_freq = sum(all_freqs) / len(all_freqs) if all_freqs else 95.0

                risk_counts = {"baixo": 0, "medio": 0, "alto": 0, "critico": 0}
                for s_data in student_records.values():
                    s_riscos = s_data["riscos"]
                    most_common = max(set(s_riscos), key=s_riscos.count).lower() if s_riscos else 'baixo'
                    risk_counts[most_common] = risk_counts.get(most_common, 0) + 1
                
                all_courses = [c for sd in student_records.values() for c in sd["cursos"]]
                all_series = [s for sd in student_records.values() for s in sd["series"]]
                
                turmas.append({
                    "id": t_code, "nome": f"Turma {t_code}",
                    "curso": max(set(all_courses), key=all_courses.count) if all_courses else "N/A",
                    "periodo": max(set(all_series), key=all_series.count) if all_series else 1,
                    "total_alunos": len(student_records), "media_turma": round(avg_media, 2),
                    "freq_media": round(avg_freq, 1), "alunos_em_alerta": risk_counts["alto"] + risk_counts["critico"],
                    "taxa_aprovacao": round(sum(1 for s in student_records.values() for sit in s["situacoes"] if sit == "Aprovado") / len(rows) * 100 if rows else 100, 1),
                    "distribuicao_risco": risk_counts
                })
            return jsonify(turmas), 200
        except Exception as e:
            return jsonify({"erro": str(e)}), 500

    @app.route("/turmas/<turma_id>/relatorio", methods=["GET"])
    @requer_autenticacao
    def relatorio_detalhado_turma(turma_id):
        # Esta rota continua a mesma, pois já usa os serviços e o banco corretamente
        # ... (código da rota relatorio_detalhado_turma)
        pass

    @app.route("/api/charts/turma/<turma_id>", methods=["GET"])
    @requer_autenticacao
    def get_turma_charts(turma_id):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT a.curso, ra.serie FROM registros_academicos ra JOIN alunos a ON ra.aluno_id = a.id WHERE ra.turma = ?", (turma_id,))
            turma_row = cursor.fetchone()
            turma_nome = f"Turma {turma_id}" + (f" ({turma_row[0]} - {turma_row[1]}º Período)" if turma_row else "")

            cursor.execute("SELECT a.nome, ra.media_final, a.frequencias, ra.serie FROM registros_academicos ra JOIN alunos a ON ra.aluno_id = a.id WHERE ra.turma = ?", (turma_id,))
            pontos_dispersao = []
            for r in cursor.fetchall():
                media, freqs_json, serie = r[1], r[2], r[3]
                freq_val = 95.0
                if freqs_json:
                    try:
                        freq_item = next((f for f in json.loads(freqs_json) if f.get("periodo") == serie), None)
                        if freq_item: freq_val = freq_item.get("percentual", 95.0)
                    except: pass
                if media is not None: pontos_dispersao.append({"nome": r[0], "media": media, "frequencia": freq_val})

            medias_turma = [p['media'] for p in pontos_dispersao]
            
            cursor.execute("SELECT ra.nome_disciplina, ra.media_final FROM registros_academicos ra WHERE ra.turma = ?", (turma_id,))
            disciplinas_raw = {}
            for r in cursor.fetchall():
                if r[0] not in disciplinas_raw: disciplinas_raw[r[0]] = []
                if r[1] is not None: disciplinas_raw[r[0]].append(r[1])
            disciplinas_data = [{"disciplina": nome, "medias": medias} for nome, medias in disciplinas_raw.items()]

            script_scatter, div_scatter = BokehService.gerar_dispersao_nota_frequencia(pontos_dispersao, turma_nome)
            script_hist, div_hist = BokehService.gerar_histograma_desempenho(medias_turma, turma_nome)
            script_box, div_box = BokehService.gerar_boxplot_disciplinas(disciplinas_data, turma_nome)

            return jsonify({
                "scatter": {"script": script_scatter, "div": div_scatter},
                "histogram": {"script": script_hist, "div": div_hist},
                "boxplot": {"script": script_box, "div": div_box},
            })
        except Exception as e:
            return jsonify({"erro": f"Erro ao gerar gráficos: {str(e)}"}), 500

    # ... (incluir todas as outras rotas: /alunos, /admin/*, /api/importar/*, etc.)

    # ------------------------------------------------------------------ #
    # Healthcheck e Tratamento de Erros
    # ------------------------------------------------------------------ #
    @app.route("/", methods=["GET"])
    def healthcheck():
        return redirect(url_for("login_page"))

    @app.errorhandler(500)
    def erro_interno(e):
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro interno do servidor."}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=True, port=int(os.environ.get("PORT", 5000)))
