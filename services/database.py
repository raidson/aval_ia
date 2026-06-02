"""
Módulo: services/database.py
Conexão e inicialização do banco SQLite para o projeto Nexus.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "simpa.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    """Cria todas as tabelas e índices se não existirem."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Migração automática: se auditoria existir e 'id' for INTEGER, dropamos para recriar como TEXT
        try:
            cur.execute("PRAGMA table_info(auditoria)")
            info = cur.fetchall()
            if info:
                id_col = [col for col in info if col[1] == "id"]
                if id_col and "INTEGER" in id_col[0][2].upper():
                    cur.execute("DROP TABLE auditoria")
                    conn.commit()
        except Exception:
            pass

        cur.executescript("""
            CREATE TABLE IF NOT EXISTS alunos (
                id                TEXT PRIMARY KEY,
                matricula         TEXT UNIQUE NOT NULL,
                nome              TEXT NOT NULL,
                curso             TEXT,
                cod_curso         INTEGER,
                periodo           INTEGER,
                ano_ingresso      INTEGER,
                sem_ingresso      INTEGER,
                unidade           TEXT,
                cidade            TEXT,
                estado            TEXT,
                sexo              TEXT,
                data_nascimento   TEXT,
                idade             INTEGER,
                prouni            TEXT,
                fies              TEXT,
                bolsa             TEXT,
                email             TEXT,
                ativo             INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS disciplinas (
                cod_disciplina    INTEGER PRIMARY KEY,
                nome              TEXT NOT NULL,
                carga_horaria     INTEGER
            );

            CREATE TABLE IF NOT EXISTS registros_academicos (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno_id          TEXT NOT NULL REFERENCES alunos(id),
                cod_disciplina    INTEGER REFERENCES disciplinas(cod_disciplina),
                nome_disciplina   TEXT,
                turma             TEXT,
                serie             INTEGER,
                ano               INTEGER NOT NULL,
                semestre          INTEGER NOT NULL,
                va1               REAL,
                va2               REAL,
                va3               REAL,
                media_final       REAL,
                media_calculada   REAL,
                situacao          TEXT CHECK(situacao IN ('Aprovado', 'Rep_Nota', 'Rep_Freq')),
                risco_academico   TEXT CHECK(risco_academico IN ('Baixo', 'Medio', 'Alto')),
                UNIQUE(aluno_id, cod_disciplina, ano, semestre)
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id          TEXT PRIMARY KEY,
                nome        TEXT NOT NULL,
                matricula   TEXT UNIQUE NOT NULL,
                perfil      TEXT NOT NULL CHECK(perfil IN ('admin', 'coordenador', 'professor', 'visualizador')),
                senha_hash  TEXT NOT NULL,
                ativo       INTEGER DEFAULT 1,
                criado_em   TEXT
            );

            CREATE TABLE IF NOT EXISTS auditoria (
                id          TEXT PRIMARY KEY,
                usuario_id  TEXT,
                acao        TEXT NOT NULL,
                recurso     TEXT,
                detalhe     TEXT,
                ip          TEXT,
                timestamp   TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS indicadores (
                id                TEXT PRIMARY KEY,
                aluno_id          TEXT NOT NULL REFERENCES alunos(id),
                tipo              TEXT NOT NULL,
                valor             REAL,
                descricao         TEXT,
                periodo           INTEGER NOT NULL,
                gerado_em         TEXT,
                UNIQUE(aluno_id, tipo, periodo)
            );

            CREATE INDEX IF NOT EXISTS idx_reg_aluno      ON registros_academicos(aluno_id);
            CREATE INDEX IF NOT EXISTS idx_reg_ano_sem    ON registros_academicos(ano, semestre);
            CREATE INDEX IF NOT EXISTS idx_reg_situacao   ON registros_academicos(situacao);
            CREATE INDEX IF NOT EXISTS idx_reg_risco      ON registros_academicos(risco_academico);
            CREATE INDEX IF NOT EXISTS idx_alunos_curso   ON alunos(curso);
        """)

        cur.execute("PRAGMA table_info(alunos)")
        colunas_alunos = [row[1] for row in cur.fetchall()]
        if "notas" not in colunas_alunos:
            cur.execute("ALTER TABLE alunos ADD COLUMN notas TEXT")
        if "frequencias" not in colunas_alunos:
            cur.execute("ALTER TABLE alunos ADD COLUMN frequencias TEXT")

        conn.commit()
    finally:
        conn.close()
