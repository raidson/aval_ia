"""
Script: data/importar_csv.py
Importa data/alunos_tratados.csv para o banco SQLite (data/simpa.db).

Uso:
    python data/importar_csv.py data/alunos_tratados.csv
"""

import sys
import os
import uuid
import sqlite3

# Garante que o root do projeto está no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pandas as pd
except ImportError:
    print("ERRO: pandas não instalado. Execute: pip install pandas")
    sys.exit(1)

from services.database import init_db, get_connection


CSV_COLUNAS = [
    "ID_ALUNO", "COD_CURSO", "NOME_CURSO", "ANO", "SEMESTRE", "SERIE",
    "ANO_INGRESSO", "SEM_INGRESSO", "COD_DISCIPLINA", "NOME_DISCIPLINA",
    "TURMA", "SITUACAO", "RISCO_ACADEMICO", "VA1", "VA2", "VA3",
    "MEDIA_FINAL", "MEDIA_CALCULADA", "DIVERGENCIA_MEDIA",
    "UNIDADE", "CIDADE", "ESTADO", "SEXO", "DATA_NASCIMENTO", "IDADE",
    "PROUNI", "FIES", "BOLSA",
]


def _nan_to_none(val):
    """Converte NaN do pandas para None (NULL no SQLite)."""
    try:
        import math
        if math.isnan(float(val)):
            return None
    except (TypeError, ValueError):
        pass
    return val


def importar(caminho_csv: str) -> None:
    print(f"Inicializando banco de dados...")
    init_db()

    print(f"Lendo CSV: {caminho_csv}")
    df = pd.read_csv(caminho_csv, sep=";", encoding="utf-8-sig", dtype=str)
    print(f"  {len(df)} linhas lidas.")

    # Normaliza nomes de colunas para maiúsculo e sem espaços extras
    df.columns = [c.strip().upper() for c in df.columns]

    conn = get_connection()
    try:
        _importar_alunos(conn, df)
        _importar_disciplinas(conn, df)
        _importar_registros(conn, df)
        conn.commit()
        _relatorio(conn)
    finally:
        conn.close()


def _importar_alunos(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    print("\nImportando alunos...")
    alunos_df = df.drop_duplicates(subset=["ID_ALUNO"])

    registros = []
    for _, row in alunos_df.iterrows():
        registros.append((
            str(uuid.uuid4()),                          # id (UUID interno)
            str(row["ID_ALUNO"]),                       # matricula
            f"Aluno {row['ID_ALUNO']}",                 # nome
            _nan_to_none(row.get("NOME_CURSO")),        # curso
            _nan_to_none(row.get("COD_CURSO")),         # cod_curso
            None,                                       # periodo
            _nan_to_none(row.get("ANO_INGRESSO")),      # ano_ingresso
            _nan_to_none(row.get("SEM_INGRESSO")),      # sem_ingresso
            _nan_to_none(row.get("UNIDADE")),           # unidade
            _nan_to_none(row.get("CIDADE")),            # cidade
            _nan_to_none(row.get("ESTADO")),            # estado
            _nan_to_none(row.get("SEXO")),              # sexo
            _nan_to_none(row.get("DATA_NASCIMENTO")),   # data_nascimento
            _nan_to_none(row.get("IDADE")),             # idade
            _nan_to_none(row.get("PROUNI")),            # prouni
            _nan_to_none(row.get("FIES")),              # fies
            _nan_to_none(row.get("BOLSA")),             # bolsa
            None,                                       # email
            1,                                          # ativo
            '[]',                                       # notas
            '[]',                                       # frequencias
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO alunos
            (id, matricula, nome, curso, cod_curso, periodo,
             ano_ingresso, sem_ingresso, unidade, cidade, estado,
             sexo, data_nascimento, idade, prouni, fies, bolsa, email, ativo,
             notas, frequencias)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, registros)
    conn.commit()
    print(f"  {len(registros)} alunos processados.")


def _importar_disciplinas(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    print("\nImportando disciplinas...")
    disc_df = df.drop_duplicates(subset=["COD_DISCIPLINA"])

    registros = []
    for _, row in disc_df.iterrows():
        cod = _nan_to_none(row.get("COD_DISCIPLINA"))
        if cod is None:
            continue
        registros.append((
            int(float(cod)),
            str(row.get("NOME_DISCIPLINA", f"Disciplina {cod}")),
            None,   # carga_horaria não está no CSV
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO disciplinas (cod_disciplina, nome, carga_horaria)
        VALUES (?,?,?)
    """, registros)
    conn.commit()
    print(f"  {len(registros)} disciplinas processadas.")


def _importar_registros(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    print("\nImportando registros acadêmicos...")

    # Monta mapa matricula → id para FK
    rows_alunos = conn.execute("SELECT id, matricula FROM alunos").fetchall()
    matricula_to_id = {r["matricula"]: r["id"] for r in rows_alunos}

    registros = []
    ignorados = 0
    for _, row in df.iterrows():
        matricula = str(row.get("ID_ALUNO", ""))
        aluno_id = matricula_to_id.get(matricula)
        if aluno_id is None:
            ignorados += 1
            continue

        cod_disc = _nan_to_none(row.get("COD_DISCIPLINA"))
        cod_disc = int(float(cod_disc)) if cod_disc is not None else None

        situacao = _nan_to_none(row.get("SITUACAO"))
        if situacao not in ("Aprovado", "Rep_Nota", "Rep_Freq"):
            situacao = None

        risco = _nan_to_none(row.get("RISCO_ACADEMICO"))
        if risco not in ("Baixo", "Medio", "Alto"):
            risco = None

        def _float(val):
            v = _nan_to_none(val)
            return float(v) if v is not None else None

        registros.append((
            aluno_id,
            cod_disc,
            _nan_to_none(row.get("NOME_DISCIPLINA")),
            _nan_to_none(row.get("TURMA")),
            _nan_to_none(row.get("SERIE")),
            _nan_to_none(row.get("ANO")),
            _nan_to_none(row.get("SEMESTRE")),
            _float(row.get("VA1")),
            _float(row.get("VA2")),
            _float(row.get("VA3")),
            _float(row.get("MEDIA_FINAL")),
            _float(row.get("MEDIA_CALCULADA")),
            situacao,
            risco,
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO registros_academicos
            (aluno_id, cod_disciplina, nome_disciplina, turma, serie,
             ano, semestre, va1, va2, va3, media_final, media_calculada,
             situacao, risco_academico)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, registros)
    conn.commit()
    print(f"  {len(registros)} registros processados ({ignorados} ignorados por aluno não encontrado).")


def _relatorio(conn: sqlite3.Connection) -> None:
    print("\n" + "=" * 50)
    print("RELATÓRIO FINAL")
    print("=" * 50)

    totais = {
        "alunos":               conn.execute("SELECT COUNT(*) FROM alunos").fetchone()[0],
        "disciplinas":          conn.execute("SELECT COUNT(*) FROM disciplinas").fetchone()[0],
        "registros_academicos": conn.execute("SELECT COUNT(*) FROM registros_academicos").fetchone()[0],
    }
    for tabela, total in totais.items():
        print(f"  {tabela}: {total} registros")

    print("\nDistribuição de risco_academico:")
    rows = conn.execute("""
        SELECT risco_academico, COUNT(*) AS total
        FROM registros_academicos
        GROUP BY risco_academico
        ORDER BY total DESC
    """).fetchall()
    for r in rows:
        label = r[0] if r[0] else "NULL"
        print(f"  {label}: {r[1]}")

    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Uso: python {sys.argv[0]} <caminho_csv>")
        sys.exit(1)
    importar(sys.argv[1])
