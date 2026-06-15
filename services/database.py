"""
Módulo: services/database.py
Configuração e gerenciamento da conexão com o banco de dados SQLite.
"""

import sqlite3
import os
from flask import g

# Define o caminho do banco de dados. Prioriza a variável de ambiente.
DATABASE_URL = os.environ.get("DATABASE_URL", "database.db")

def get_connection():
    """
    Abre uma nova conexão com o banco de dados se não houver uma no contexto da aplicação.
    Reutiliza a conexão existente se já estiver no contexto 'g' do Flask.
    """
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_URL)
        db.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    return db

def close_connection(exception=None):
    """
    Fecha a conexão com o banco de dados ao final da requisição.
    Esta função é ideal para ser registrada com o 'app.teardown_appcontext'.
    """
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

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
            periodo INTEGER NOT NULL,
            iaa REAL,
            irp REAL,
            ira REAL,
            percentil REAL,
            zscore REAL,
            risco TEXT,
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
