"""
Módulo: services/database.py
Configuração e gerenciamento da conexão com o banco de dados SQLite.
"""

import sqlite3
import os
from flask import g, current_app, has_app_context

# Define o caminho do banco de dados. Prioriza a variável de ambiente.
DATABASE_URL = os.environ.get("DATABASE_URL", "database.db")

_local_db = None

def get_connection():
    """
    Abre uma nova conexão com o banco de dados se não houver uma no contexto da aplicação.
    Reutiliza a conexão existente se já estiver no contexto 'g' do Flask.
    Suporta execução fora do contexto Flask para scripts/testes.
    """
    global _local_db
    if has_app_context():
        db = getattr(g, "_database", None)
        try:
            if db is not None:
                db.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            db = g._database = None

        if db is None:
            db_url = current_app.config.get("DATABASE_URL", DATABASE_URL)
            if db_url.startswith("sqlite:///"):
                db_url = db_url.replace("sqlite:///", "")
            db = g._database = sqlite3.connect(db_url)
            db.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
        return db
    else:
        # Fora do contexto da aplicação (ex: scripts, seed, testes fora do flask request)
        try:
            if _local_db is not None:
                _local_db.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            _local_db = None

        if _local_db is None:
            db_url = DATABASE_URL
            if db_url.startswith("sqlite:///"):
                db_url = db_url.replace("sqlite:///", "")
            _local_db = sqlite3.connect(db_url)
            _local_db.row_factory = sqlite3.Row
        return _local_db

def close_connection(exception=None):
    """
    Fecha a conexão com o banco de dados ao final da requisição.
    Esta função é ideal para ser registrada com o 'app.teardown_appcontext'.
    """
    global _local_db
    if has_app_context():
        db = getattr(g, "_database", None)
        if db is not None:
            db.close()
    else:
        if _local_db is not None:
            _local_db.close()
            _local_db = None

def init_db():
    """
    Inicializa o banco de dados criando as tabelas necessárias se elas não existirem.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id TEXT PRIMARY KEY,
            matricula TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            curso TEXT,
            periodo INTEGER,
            ano_ingresso INTEGER,
            sem_ingresso INTEGER,
            cod_curso INTEGER,
            unidade TEXT,
            cidade TEXT,
            estado TEXT,
            sexo TEXT,
            data_nascimento TEXT,
            idade INTEGER,
            prouni TEXT,
            fies TEXT,
            bolsa TEXT,
            email TEXT,
            ativo BOOLEAN DEFAULT TRUE,
            notas TEXT,
            frequencias TEXT
        )
    """)

    # Tabela de Disciplinas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_disciplina INTEGER UNIQUE,
            nome TEXT NOT NULL,
            carga_horaria INTEGER
        )
    """)

    # Tabela de Registros Acadêmicos (Fatos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros_academicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id TEXT NOT NULL,
            cod_disciplina INTEGER,
            nome_disciplina TEXT,
            turma TEXT,
            serie INTEGER,
            ano INTEGER,
            semestre INTEGER,
            va1 REAL,
            va2 REAL,
            va3 REAL,
            media_final REAL,
            media_calculada REAL,
            situacao TEXT,
            risco_academico TEXT,
            FOREIGN KEY (aluno_id) REFERENCES alunos (id)
        )
    """)

    # Tabela de Indicadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicadores (
            id TEXT PRIMARY KEY,
            aluno_id TEXT NOT NULL,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            periodo INTEGER NOT NULL,
            gerado_em TEXT,
            FOREIGN KEY (aluno_id) REFERENCES alunos (id)
        )
    """)

    # Tabela de Usuários para controle de acesso
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            matricula TEXT UNIQUE NOT NULL,
            email TEXT,
            perfil TEXT NOT NULL,
            cursos TEXT,
            senha_hash TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE
        )
    """)

    # Tabela de Auditoria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id TEXT PRIMARY KEY,
            usuario_id TEXT,
            acao TEXT NOT NULL,
            detalhe TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    if not has_app_context():
        conn.close()
