"""
Módulo: api/app.py
API REST do Nexus construída com Flask.
Expõe os recursos: /alunos, /turmas, /indicadores, /relatorios
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

from services.repositorio import Repositorio
from services.aluno_service import AlunoService
from services.indicador_service import IndicadorService
from services.lyceum_service import LyceumService
from models.usuario import Usuario, PerfilUsuario

# ------------------------------------------------------------------ #
# Inicialização
# ------------------------------------------------------------------ #

app = Flask(__name__)

# Repositórios
repo_alunos      = Repositorio("data/alunos.json")
repo_turmas      = Repositorio("data/turmas.json")
repo_indicadores = Repositorio("data/indicadores.json")
repo_usuarios    = Repositorio("data/usuarios.json")

# Serviços
aluno_service     = AlunoService(repo_alunos)
indicador_service = IndicadorService(repo_indicadores)
lyceum_service    = LyceumService()

# Tokens de sessão ativos {token: usuario_id}
_tokens_ativos: dict = {}

# ------------------------------------------------------------------ #
# Autenticação simples (token no header)
# ------------------------------------------------------------------ #

def requer_autenticacao(f):
    """Decorator: exige token válido no header Authorization."""
    @wraps(f)
    def decorado(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token not in _tokens_ativos:
            return jsonify({"erro": "Não autorizado. Token inválido ou ausente."}), 401
        return f(*args, **kwargs)
    return decorado


def requer_permissao(acao: str):
    """Decorator: verifica se o usuário tem permissão para a ação."""
    def decorator(f):
        @wraps(f)
        def decorado(*args, **kwargs):
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            usuario_id = _tokens_ativos.get(token)
            dados_usuario = repo_usuarios.buscar(usuario_id)
            if not dados_usuario:
                return jsonify({"erro": "Usuário não encontrado."}), 403
            perfil = PerfilUsuario(dados_usuario["perfil"])
            usuario = Usuario(
                id=dados_usuario["id"],
                nome=dados_usuario["nome"],
                matricula=dados_usuario.get("matricula", ""),
                perfil=perfil,
            )
            if not usuario.tem_permissao(acao):
                return jsonify({"erro": f"Permissão negada para ação: {acao}"}), 403
            return f(*args, **kwargs)
        return decorado
    return decorator


# ------------------------------------------------------------------ #
# Rotas de interface gráfica (Frontend)
# ------------------------------------------------------------------ #

@app.route("/login", methods=["GET"])
def login_page():
    """
    GET /login
    Retorna a página HTML de login.
    """
    return render_template("login.html")


@app.route("/dashboard", methods=["GET"])
def dashboard_page():
    """
    GET /dashboard
    Retorna a página de Dashboard analítico.
    """
    return render_template("dashboard.html")


# ------------------------------------------------------------------ #
# Rotas de autenticação
# ------------------------------------------------------------------ #

@app.route("/auth/login", methods=["POST"])
def login():
    """
    POST /auth/login
    Body: { "matricula": "...", "senha": "..." }
    Retorna token de acesso.
    """
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


@app.route("/auth/logout", methods=["POST"])
@requer_autenticacao
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    _tokens_ativos.pop(token, None)
    return jsonify({"mensagem": "Logout realizado com sucesso."}), 200


# ------------------------------------------------------------------ #
# Rotas de alunos  /alunos
# ------------------------------------------------------------------ #

@app.route("/alunos", methods=["GET"])
@requer_autenticacao
def listar_alunos():
    """GET /alunos — lista todos os alunos."""
    periodo = request.args.get("periodo", type=int)
    if periodo:
        alunos = aluno_service.listar_por_periodo(periodo)
    else:
        alunos = aluno_service.listar_todos()
    return jsonify([a.to_dict() for a in alunos]), 200


@app.route("/alunos/<aluno_id>", methods=["GET"])
@requer_autenticacao
def buscar_aluno(aluno_id):
    """GET /alunos/<id> — retorna um aluno específico."""
    try:
        aluno = aluno_service.buscar_por_id(aluno_id)
        return jsonify(aluno.to_dict()), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 404


@app.route("/alunos", methods=["POST"])
@requer_autenticacao
@requer_permissao("escrita")
def cadastrar_aluno():
    """
    POST /alunos
    Body: { "nome", "matricula", "curso", "periodo", "email"(opcional) }
    """
    dados = request.get_json()
    campos_obrigatorios = ["nome", "matricula", "curso", "periodo"]
    for campo in campos_obrigatorios:
        if campo not in dados:
            return jsonify({"erro": f"Campo obrigatório ausente: {campo}"}), 400
    try:
        aluno = aluno_service.cadastrar(**dados)
        return jsonify(aluno.to_dict()), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 409


@app.route("/alunos/<aluno_id>/notas", methods=["POST"])
@requer_autenticacao
@requer_permissao("escrita")
def registrar_nota(aluno_id):
    """
    POST /alunos/<id>/notas
    Body: { "disciplina", "nota", "periodo" }
    """
    dados = request.get_json()
    try:
        aluno = aluno_service.registrar_nota(
            aluno_id,
            dados["disciplina"],
            float(dados["nota"]),
            int(dados["periodo"]),
        )
        return jsonify(aluno.to_dict()), 200
    except (ValueError, KeyError) as e:
        return jsonify({"erro": str(e)}), 400


@app.route("/alunos/<aluno_id>/frequencias", methods=["POST"])
@requer_autenticacao
@requer_permissao("escrita")
def registrar_frequencia(aluno_id):
    """
    POST /alunos/<id>/frequencias
    Body: { "disciplina", "percentual", "periodo" }
    """
    dados = request.get_json()
    try:
        aluno = aluno_service.registrar_frequencia(
            aluno_id,
            dados["disciplina"],
            float(dados["percentual"]),
            int(dados["periodo"]),
        )
        return jsonify(aluno.to_dict()), 200
    except (ValueError, KeyError) as e:
        return jsonify({"erro": str(e)}), 400


# ------------------------------------------------------------------ #
# Rotas de indicadores  /indicadores
# ------------------------------------------------------------------ #

@app.route("/indicadores/<aluno_id>", methods=["GET"])
@requer_autenticacao
def listar_indicadores(aluno_id):
    """GET /indicadores/<aluno_id> — retorna indicadores calculados."""
    indicadores = indicador_service.listar_indicadores_aluno(aluno_id)
    return jsonify([i.to_dict() for i in indicadores]), 200


@app.route("/indicadores/<aluno_id>/gerar", methods=["POST"])
@requer_autenticacao
@requer_permissao("escrita")
def gerar_indicadores(aluno_id):
    """POST /indicadores/<aluno_id>/gerar — calcula e salva indicadores."""
    dados = request.get_json() or {}
    periodo = dados.get("periodo", 1)
    try:
        aluno = aluno_service.buscar_por_id(aluno_id)
        indicadores = indicador_service.gerar_indicadores_aluno(aluno, periodo)
        return jsonify([i.to_dict() for i in indicadores]), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 404


@app.route("/indicadores/<aluno_id>/risco", methods=["GET"])
@requer_autenticacao
def calcular_risco(aluno_id):
    """GET /indicadores/<aluno_id>/risco — classifica o risco acadêmico."""
    periodo = request.args.get("periodo", 1, type=int)
    try:
        aluno = aluno_service.buscar_por_id(aluno_id)
        risco = indicador_service.classificar_risco(aluno, periodo)
        return jsonify(risco.to_dict()), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 404


# ------------------------------------------------------------------ #
# Integração Lyceum
# ------------------------------------------------------------------ #

@app.route("/sync/lyceum", methods=["POST"])
@requer_autenticacao
def sincronizar_lyceum():
    """
    POST /sync/lyceum
    Body: { "url", "usuario", "senha" }
    """
    dados = request.get_json()
    if not all(k in dados for k in ("url", "usuario", "senha")):
        return jsonify({"erro": "URL, usuário e senha são obrigatórios."}), 400

    sucesso, mensagem = lyceum_service.autenticar(dados["url"], dados["usuario"], dados["senha"])
    if not sucesso:
        return jsonify({"erro": mensagem}), 401

    # Extrai os dados (Simulado por enquanto, até termos o parse real)
    novas_notas = lyceum_service.extrair_notas(dados["url"])
    
    # Exemplo de como isso atualizaria o banco (lógica a ser refinada)
    # for nota in novas_notas:
    #     aluno_service.registrar_nota(...)

    return jsonify({"mensagem": "Sincronização concluída com sucesso (Modo: Estrutura)", "sucesso": True}), 200


# ------------------------------------------------------------------ #
# Relatórios
# ------------------------------------------------------------------ #

@app.route("/relatorios/turma", methods=["GET"])
@requer_autenticacao
@requer_permissao("relatorios")
def relatorio_turma():
    """GET /relatorios/turma?periodo=1 — relatório consolidado por aluno."""
    periodo = request.args.get("periodo", 1, type=int)
    alunos = aluno_service.listar_por_periodo(periodo)
    todos = alunos
    relatorio = []
    for aluno in alunos:
        media = indicador_service.calcular_media_geral(aluno, periodo)
        freq  = indicador_service.calcular_frequencia_media(aluno, periodo)
        risco     = indicador_service.classificar_risco(aluno, periodo)
        zscore    = indicador_service.calcular_zscore_aluno(todos, aluno.id, periodo)
        percentil = indicador_service.calcular_percentil_aluno(todos, aluno.id, periodo)
        iaa       = indicador_service.calcular_iaa(aluno, periodo)
        irp       = indicador_service.calcular_irp(aluno, periodo)
        relatorio.append({
            "aluno_id":        aluno.id,
            "nome":            aluno.nome,
            "matricula":       aluno.matricula,
            "media_geral":     media,
            "frequencia_media": freq,
            "iaa":             iaa,
            "irp":             irp,
            "risco":           risco.nivel.value,
            "zscore":          zscore,
            "percentil":       percentil,
        })
    return jsonify({"periodo": periodo, "total": len(relatorio), "alunos": relatorio}), 200


@app.route("/relatorios/estatisticas", methods=["GET"])
@requer_autenticacao
@requer_permissao("relatorios")
def estatisticas_turma():
    """GET /relatorios/estatisticas?periodo=1 — estatísticas descritivas da turma."""
    periodo = request.args.get("periodo", 1, type=int)
    alunos = aluno_service.listar_por_periodo(periodo)
    stats = indicador_service.calcular_estatisticas_turma(alunos, periodo)
    correlacao = indicador_service.calcular_correlacao_freq_nota(alunos, periodo)
    distribuicao = indicador_service.calcular_distribuicao_medias(alunos, periodo)
    pontos = indicador_service.calcular_pontos_dispersao(alunos, periodo)
    return jsonify({
        "periodo": periodo,
        "estatisticas_turma": stats,
        "correlacao_freq_nota": correlacao,
        "interpretacao_correlacao": _interpretar_correlacao(correlacao),
        "distribuicao_medias": distribuicao,
        "pontos_dispersao": pontos,
    }), 200


@app.route("/relatorios/disciplinas", methods=["GET"])
@requer_autenticacao
@requer_permissao("relatorios")
def estatisticas_disciplinas():
    """GET /relatorios/disciplinas?periodo=1 — estatísticas por disciplina."""
    periodo = request.args.get("periodo", 1, type=int)
    alunos = aluno_service.listar_por_periodo(periodo)
    stats = indicador_service.calcular_estatisticas_por_disciplina(alunos, periodo)
    return jsonify({"periodo": periodo, "disciplinas": stats}), 200


@app.route("/indicadores/<aluno_id>/perfil", methods=["GET"])
@requer_autenticacao
def perfil_analitico(aluno_id):
    """GET /indicadores/<id>/perfil?periodo=1 — perfil analítico completo do aluno."""
    periodo = request.args.get("periodo", 1, type=int)
    try:
        aluno  = aluno_service.buscar_por_id(aluno_id)
        todos  = aluno_service.listar_por_periodo(periodo)
        risco  = indicador_service.classificar_risco(aluno, periodo)
        extremas = indicador_service.calcular_notas_extremas(aluno, periodo)
        quartis  = indicador_service.calcular_quartis(aluno, periodo)
        return jsonify({
            "aluno": {"id": aluno.id, "nome": aluno.nome, "matricula": aluno.matricula},
            "periodo": periodo,
            "indicadores": {
                # Tendência central
                "media_geral":          indicador_service.calcular_media_geral(aluno, periodo),
                "mediana":              indicador_service.calcular_mediana(aluno, periodo),
                # Dispersão
                "desvio_padrao":        indicador_service.calcular_desvio_padrao(aluno, periodo),
                "coeficiente_variacao": indicador_service.calcular_coeficiente_variacao(aluno, periodo),
                "amplitude":            indicador_service.calcular_amplitude(aluno, periodo),
                "q1":                   quartis["q1"],
                "q3":                   quartis["q3"],
                "iqr":                  quartis["iqr"],
                # Forma da distribuição
                "assimetria":           indicador_service.calcular_assimetria(aluno, periodo),
                "curtose":              indicador_service.calcular_curtose(aluno, periodo),
                # Extremos
                "nota_minima":          extremas["min"],
                "nota_maxima":          extremas["max"],
                # Frequência e aproveitamento
                "frequencia_media":     indicador_service.calcular_frequencia_media(aluno, periodo),
                "iaa":                  indicador_service.calcular_iaa(aluno, periodo),
                "nota_efetiva":         indicador_service.calcular_nota_efetiva(aluno, periodo),
                # Comparativo e risco
                "zscore_turma":         indicador_service.calcular_zscore_aluno(todos, aluno_id, periodo),
                "percentil_turma":      indicador_service.calcular_percentil_aluno(todos, aluno_id, periodo),
                "irp":                  indicador_service.calcular_irp(aluno, periodo),
            },
            "notas_por_disciplina": indicador_service.calcular_notas_por_disciplina(aluno, periodo),
            "tendencia":            indicador_service.calcular_tendencia_periodo(aluno),
            "risco":                risco.to_dict(),
        }), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 404


@app.route("/relatorios/turma/exportar", methods=["GET"])
@requer_autenticacao
@requer_permissao("relatorios")
def exportar_relatorio_turma_excel():
    """GET /relatorios/turma/exportar?periodo=1 — exporta o relatório de turma em Excel."""
    periodo = request.args.get("periodo", 1, type=int)
    alunos = aluno_service.listar_por_periodo(periodo)
    todos = alunos

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Turma - Período {periodo}"

    cabecalho = ["Nome", "Matrícula", "Média Geral", "Frequência (%)", "IAA", "IRP", "Z-Score", "Percentil", "Risco"]
    ws.append(cabecalho)

    # Estilo do cabeçalho
    azul = PatternFill("solid", fgColor="2563EB")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = azul
        cell.alignment = Alignment(horizontal="center")

    cores_risco = {"alto": "FCA5A5", "medio": "FDE68A", "baixo": "BBF7D0"}

    for aluno in alunos:
        media     = indicador_service.calcular_media_geral(aluno, periodo)
        freq      = indicador_service.calcular_frequencia_media(aluno, periodo)
        iaa       = indicador_service.calcular_iaa(aluno, periodo)
        irp       = indicador_service.calcular_irp(aluno, periodo)
        zscore    = indicador_service.calcular_zscore_aluno(todos, aluno.id, periodo)
        percentil = indicador_service.calcular_percentil_aluno(todos, aluno.id, periodo)
        risco     = indicador_service.classificar_risco(aluno, periodo)

        linha = [
            aluno.nome,
            aluno.matricula,
            round(media, 2) if media is not None else "",
            round(freq, 1) if freq is not None else "",
            round(iaa, 3) if iaa is not None else "",
            round(irp, 3) if irp is not None else "",
            round(zscore, 3) if zscore is not None else "",
            round(percentil, 1) if percentil is not None else "",
            risco.nivel.value,
        ]
        ws.append(linha)

        # Cor na célula de risco (última coluna)
        nivel = risco.nivel.value
        if nivel in cores_risco:
            ws.cell(row=ws.max_row, column=9).fill = PatternFill("solid", fgColor=cores_risco[nivel])

    # Ajuste de largura das colunas
    larguras = [30, 14, 13, 16, 10, 10, 10, 10, 10]
    for i, w in enumerate(larguras, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"relatorio_turma_periodo{periodo}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/relatorios/alunos/exportar", methods=["GET"])
@requer_autenticacao
@requer_permissao("relatorios")
def exportar_alunos_excel():
    """GET /relatorios/alunos/exportar?periodo=1 — exporta lista de alunos com notas e frequências em Excel."""
    periodo = request.args.get("periodo", type=int)
    alunos = aluno_service.listar_por_periodo(periodo) if periodo else aluno_service.listar_todos()

    wb = openpyxl.Workbook()

    # Aba: Alunos
    ws_alunos = wb.active
    ws_alunos.title = "Alunos"
    cab_alunos = ["Nome", "Matrícula", "Curso", "Período", "Email"]
    ws_alunos.append(cab_alunos)
    azul = PatternFill("solid", fgColor="2563EB")
    for cell in ws_alunos[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = azul
        cell.alignment = Alignment(horizontal="center")
    for aluno in alunos:
        ws_alunos.append([aluno.nome, aluno.matricula, aluno.curso, aluno.periodo, aluno.email or ""])
    for i, w in enumerate([30, 14, 25, 10, 30], 1):
        ws_alunos.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # Aba: Notas
    ws_notas = wb.create_sheet("Notas")
    cab_notas = ["Nome", "Matrícula", "Disciplina", "Nota", "Período"]
    ws_notas.append(cab_notas)
    for cell in ws_notas[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = azul
        cell.alignment = Alignment(horizontal="center")
    for aluno in alunos:
        for n in aluno.get_notas():
            ws_notas.append([aluno.nome, aluno.matricula, n["disciplina"], n["nota"], n["periodo"]])
    for i, w in enumerate([30, 14, 25, 8, 10], 1):
        ws_notas.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # Aba: Frequências
    ws_freq = wb.create_sheet("Frequências")
    cab_freq = ["Nome", "Matrícula", "Disciplina", "Frequência (%)", "Período"]
    ws_freq.append(cab_freq)
    for cell in ws_freq[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = azul
        cell.alignment = Alignment(horizontal="center")
    for aluno in alunos:
        for f in aluno.get_frequencias():
            ws_freq.append([aluno.nome, aluno.matricula, f["disciplina"], f["percentual"], f["periodo"]])
    for i, w in enumerate([30, 14, 25, 14, 10], 1):
        ws_freq.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    nome_arquivo = f"alunos_periodo{periodo}.xlsx" if periodo else "alunos_todos.xlsx"
    return send_file(
        buf,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _interpretar_correlacao(r: float) -> str:
    """Retorna texto interpretativo para o coeficiente de correlação de Pearson."""
    abs_r = abs(r)
    direcao = "positiva" if r >= 0 else "negativa"
    if abs_r >= 0.9:
        forca = "muito forte"
    elif abs_r >= 0.7:
        forca = "forte"
    elif abs_r >= 0.5:
        forca = "moderada"
    elif abs_r >= 0.3:
        forca = "fraca"
    else:
        forca = "muito fraca ou inexistente"
    return f"Correlação {direcao} {forca} (r={r})"


# ------------------------------------------------------------------ #
# Painel Admin — Gestão de Usuários
# ------------------------------------------------------------------ #

@app.route("/admin", methods=["GET"])
def admin_page():
    return render_template("dashboard.html")


@app.route("/admin/usuarios", methods=["GET"])
@requer_autenticacao
@requer_permissao("usuarios")
def admin_listar_usuarios():
    usuarios = repo_usuarios.listar()
    return jsonify([{
        "id": u["id"],
        "nome": u["nome"],
        "matricula": u["matricula"],
        "perfil": u["perfil"],
        "ativo": u.get("ativo", True),
    } for u in usuarios]), 200


@app.route("/admin/usuarios", methods=["POST"])
@requer_autenticacao
@requer_permissao("usuarios")
def admin_criar_usuario():
    dados = request.get_json() or {}
    campos = ["nome", "matricula", "senha", "perfil"]
    for c in campos:
        if c not in dados:
            return jsonify({"erro": f"Campo obrigatório ausente: {c}"}), 400
    perfis_validos = ["admin", "professor", "coordenador", "visualizador"]
    if dados["perfil"] not in perfis_validos:
        return jsonify({"erro": f"Perfil inválido. Use: {', '.join(perfis_validos)}"}), 400
    existente = repo_usuarios.filtrar("matricula", dados["matricula"])
    if existente:
        return jsonify({"erro": "Matrícula já cadastrada."}), 409
    novo_id = str(uuid.uuid4())
    usuario = {
        "id": novo_id,
        "nome": dados["nome"],
        "matricula": dados["matricula"],
        "perfil": dados["perfil"],
        "senha_hash": hashlib.sha256(dados["senha"].encode()).hexdigest(),
        "ativo": True,
    }
    repo_usuarios.salvar(novo_id, usuario)
    return jsonify({"id": novo_id, "nome": usuario["nome"], "matricula": usuario["matricula"], "perfil": usuario["perfil"], "ativo": True}), 201


@app.route("/admin/usuarios/<usuario_id>", methods=["PUT"])
@requer_autenticacao
@requer_permissao("usuarios")
def admin_atualizar_usuario(usuario_id):
    dados = request.get_json() or {}
    usuario = repo_usuarios.buscar(usuario_id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    if "perfil" in dados:
        perfis_validos = ["admin", "professor", "coordenador", "visualizador"]
        if dados["perfil"] not in perfis_validos:
            return jsonify({"erro": "Perfil inválido."}), 400
        usuario["perfil"] = dados["perfil"]
    if "ativo" in dados:
        usuario["ativo"] = bool(dados["ativo"])
    if "senha" in dados and dados["senha"]:
        usuario["senha_hash"] = hashlib.sha256(dados["senha"].encode()).hexdigest()
    if "nome" in dados:
        usuario["nome"] = dados["nome"]
    repo_usuarios.salvar(usuario_id, usuario)
    return jsonify({"mensagem": "Usuário atualizado.", "id": usuario_id}), 200


@app.route("/admin/usuarios/<usuario_id>", methods=["DELETE"])
@requer_autenticacao
@requer_permissao("usuarios")
def admin_deletar_usuario(usuario_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if _tokens_ativos.get(token) == usuario_id:
        return jsonify({"erro": "Você não pode remover sua própria conta."}), 400
    removido = repo_usuarios.deletar(usuario_id)
    if not removido:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return jsonify({"mensagem": "Usuário removido."}), 200


# ------------------------------------------------------------------ #
# Alertas Inteligentes
# ------------------------------------------------------------------ #

@app.route("/alertas", methods=["GET"])
@requer_autenticacao
def gerar_alertas():
    """GET /alertas?periodo=2 — detecta padrões de risco e gera alertas automáticos."""
    periodo = request.args.get("periodo", 2, type=int)
    alunos = aluno_service.listar_por_periodo(periodo)
    todos = alunos
    alertas = []

    for aluno in alunos:
        freq  = indicador_service.calcular_frequencia_media(aluno, periodo)
        media = indicador_service.calcular_media_geral(aluno, periodo)
        cv    = indicador_service.calcular_coeficiente_variacao(aluno, periodo)
        zscore = indicador_service.calcular_zscore_aluno(todos, aluno.id, periodo)

        # Sem dados no período — ignora
        if freq == 0.0 and media == 0.0:
            continue

        # Frequência crítica (abaixo do mínimo legal)
        if freq < 75:
            alertas.append({
                "nivel": "critico",
                "aluno_id": aluno.id,
                "aluno_nome": aluno.nome,
                "tipo": "frequencia",
                "mensagem": f"Frequência crítica: {freq:.1f}% — abaixo do mínimo de 75%",
                "acao": "Contato urgente e elaboração de plano de reposição",
            })
        elif freq < 82:
            alertas.append({
                "nivel": "alto",
                "aluno_id": aluno.id,
                "aluno_nome": aluno.nome,
                "tipo": "frequencia",
                "mensagem": f"Frequência em atenção: {freq:.1f}% — próxima do limite mínimo",
                "acao": "Monitorar assiduidade e conversar com o aluno",
            })

        # Desempenho abaixo do mínimo de aprovação
        if media < 5.0:
            alertas.append({
                "nivel": "critico",
                "aluno_id": aluno.id,
                "aluno_nome": aluno.nome,
                "tipo": "desempenho",
                "mensagem": f"Média abaixo do mínimo: {media:.2f} — risco de reprovação",
                "acao": "Agendar tutoria individual e reforço nas disciplinas críticas",
            })
        elif media < 6.5:
            alertas.append({
                "nivel": "alto",
                "aluno_id": aluno.id,
                "aluno_nome": aluno.nome,
                "tipo": "desempenho",
                "mensagem": f"Média em zona de risco: {media:.2f}",
                "acao": "Incentivar participação e verificar dificuldades específicas",
            })

        # Desempenho inconsistente entre disciplinas
        if cv is not None and cv > 35:
            alertas.append({
                "nivel": "medio",
                "aluno_id": aluno.id,
                "aluno_nome": aluno.nome,
                "tipo": "inconsistencia",
                "mensagem": f"Desempenho muito irregular entre disciplinas (CV: {cv:.1f}%)",
                "acao": "Identificar disciplinas com maior dificuldade e direcionar suporte",
            })

        # Desempenho muito abaixo da média da turma
        if zscore is not None and zscore < -1.5:
            alertas.append({
                "nivel": "alto",
                "aluno_id": aluno.id,
                "aluno_nome": aluno.nome,
                "tipo": "comparativo",
                "mensagem": f"Desempenho {abs(zscore):.1f} desvios abaixo da média da turma (z={zscore:.2f})",
                "acao": "Avaliar necessidade de acompanhamento pedagógico especializado",
            })

    ordem = {"critico": 0, "alto": 1, "medio": 2}
    alertas.sort(key=lambda a: ordem.get(a["nivel"], 3))

    return jsonify({"periodo": periodo, "total": len(alertas), "alertas": alertas}), 200


# ------------------------------------------------------------------ #
# Healthcheck
# ------------------------------------------------------------------ #

@app.route("/", methods=["GET"])
def healthcheck():
    return redirect(url_for("login_page"))


# ------------------------------------------------------------------ #
# Tratamento global de erros
# ------------------------------------------------------------------ #

@app.errorhandler(404)
def nao_encontrado(e):
    return jsonify({"erro": "Rota não encontrada."}), 404

@app.errorhandler(405)
def metodo_nao_permitido(e):
    return jsonify({"erro": "Método HTTP não permitido para esta rota."}), 405

@app.errorhandler(500)
def erro_interno(e):
    return jsonify({"erro": "Erro interno do servidor."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", debug=True, port=port)
