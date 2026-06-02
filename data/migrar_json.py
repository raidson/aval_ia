"""
Script: data/migrar_json.py
Migra os dados dos arquivos JSON existentes para o banco SQLite (data/simpa.db).

Uso:
    python data/migrar_json.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.database import init_db, get_connection

DATA_DIR = os.path.join(os.path.dirname(__file__))


def _ler_json(nome: str) -> dict:
    caminho = os.path.join(DATA_DIR, nome)
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def migrar_alunos(conn) -> int:
    dados = _ler_json("alunos.json")
    if not dados:
        print("  alunos.json vazio ou não encontrado.")
        return 0

    registros = []
    for aluno in dados.values():
        notas = aluno.get("notas")
        frequencias = aluno.get("frequencias")
        registros.append((
            aluno["id"],
            aluno.get("matricula"),
            aluno.get("nome"),
            aluno.get("curso"),
            aluno.get("cod_curso"),
            aluno.get("periodo"),
            aluno.get("ano_ingresso"),
            aluno.get("sem_ingresso"),
            aluno.get("unidade"),
            aluno.get("cidade"),
            aluno.get("estado"),
            aluno.get("sexo"),
            aluno.get("data_nascimento"),
            aluno.get("idade"),
            aluno.get("prouni"),
            aluno.get("fies"),
            aluno.get("bolsa"),
            aluno.get("email"),
            1 if aluno.get("ativo", True) else 0,
            json.dumps(notas if notas is not None else [], ensure_ascii=False),
            json.dumps(frequencias if frequencias is not None else [], ensure_ascii=False),
        ))

    conn.executemany("""
        INSERT OR REPLACE INTO alunos
            (id, matricula, nome, curso, cod_curso, periodo,
             ano_ingresso, sem_ingresso, unidade, cidade, estado,
             sexo, data_nascimento, idade, prouni, fies, bolsa,
             email, ativo, notas, frequencias)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, registros)
    return len(registros)


def migrar_usuarios(conn) -> int:
    dados = _ler_json("usuarios.json")
    if not dados:
        print("  usuarios.json vazio ou não encontrado.")
        return 0

    registros = []
    for u in dados.values():
        registros.append((
            u["id"],
            u.get("nome"),
            u.get("matricula"),
            u.get("perfil", "visualizador"),
            u.get("senha_hash"),
            1 if u.get("ativo", True) else 0,
            u.get("criado_em"),
        ))

    conn.executemany("""
        INSERT OR REPLACE INTO usuarios
            (id, nome, matricula, perfil, senha_hash, ativo, criado_em)
        VALUES (?,?,?,?,?,?,?)
    """, registros)
    return len(registros)


def migrar_auditoria(conn) -> int:
    dados = _ler_json("auditoria.json")
    registros = [v for v in dados.values() if isinstance(v, dict)]
    if not registros:
        return 0

    for reg in registros:
        conn.execute("""
            INSERT OR IGNORE INTO auditoria
                (usuario_id, acao, recurso, detalhe, ip, timestamp)
            VALUES (?,?,?,?,?,?)
        """, (
            reg.get("usuario_id"),
            reg.get("acao", ""),
            reg.get("recurso"),
            reg.get("detalhe"),
            reg.get("ip"),
            reg.get("timestamp"),
        ))
    return len(registros)


def main():
    print("Inicializando banco de dados...")
    init_db()

    conn = get_connection()
    try:
        print("\nMigrando alunos...")
        n = migrar_alunos(conn)
        conn.commit()
        print(f"  {n} alunos inseridos.")

        print("\nMigrando usuarios...")
        n = migrar_usuarios(conn)
        conn.commit()
        print(f"  {n} usuarios inseridos.")

        print("\nMigrando auditoria...")
        n = migrar_auditoria(conn)
        conn.commit()
        print(f"  {n} registros de auditoria inseridos.")

        print("\n" + "=" * 40)
        print("RESULTADO FINAL")
        print("=" * 40)
        for tabela in ("alunos", "usuarios", "auditoria", "disciplinas", "registros_academicos"):
            total = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            print(f"  {tabela}: {total}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
