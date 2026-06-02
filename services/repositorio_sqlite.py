"""
Módulo: services/repositorio_sqlite.py
Repositório genérico com persistência em SQLite.
Interface compatível com services/repositorio.py (JSON).
"""

import json
from typing import Optional
from services.database import get_connection

# Colunas que identificam o registro principal de cada tabela.
# Necessário porque tabelas diferentes usam nomes de PK distintos.
_PK_MAP = {
    "alunos":               "id",
    "disciplinas":          "cod_disciplina",
    "registros_academicos": "id",
    "usuarios":             "id",
    "auditoria":            "id",
    "indicadores":          "id",
}


class RepositorioSQLite:
    """Repositório genérico com persistência em SQLite."""

    def __init__(self, tabela: str):
        self._tabela = tabela
        self._pk = _PK_MAP.get(tabela, "id")

    def _serialize(self, valor):
        if isinstance(valor, (dict, list)):
            return json.dumps(valor, ensure_ascii=False)
        return valor

    def _deserialize(self, valor):
        if isinstance(valor, str) and valor and valor[0] in ('{', '['):
            try:
                return json.loads(valor)
            except json.JSONDecodeError:
                return valor
        return valor

    def _parse_row(self, row):
        dados = dict(row)
        return {k: self._deserialize(v) for k, v in dados.items()}

    # ------------------------------------------------------------------ #
    # Interface pública compatível com Repositorio JSON
    # ------------------------------------------------------------------ #

    def salvar(self, id, entidade_dict: dict) -> None:
        """Upsert: insere ou substitui o registro completo."""
        dados = {k: self._serialize(v) for k, v in entidade_dict.items()}
        dados[self._pk] = id
        cols = ", ".join(dados.keys())
        placeholders = ", ".join("?" * len(dados))
        sql = f"INSERT OR REPLACE INTO {self._tabela} ({cols}) VALUES ({placeholders})"
        with get_connection() as conn:
            conn.execute(sql, list(dados.values()))
            conn.commit()

    def salvar_lote(self, itens: list) -> None:
        """Upsert em lote: insere ou substitui múltiplos registros em uma única transação."""
        if not itens:
            return
        primeiro_id, primeiro_dict = itens[0]
        dados_primeiro = {k: self._serialize(v) for k, v in primeiro_dict.items()}
        dados_primeiro[self._pk] = primeiro_id
        cols = ", ".join(dados_primeiro.keys())
        placeholders = ", ".join("?" * len(dados_primeiro))
        sql = f"INSERT OR REPLACE INTO {self._tabela} ({cols}) VALUES ({placeholders})"
        
        parametros = []
        for id_, entidade_dict in itens:
            dados = {k: self._serialize(v) for k, v in entidade_dict.items()}
            dados[self._pk] = id_
            parametros.append(list(dados.values()))
            
        with get_connection() as conn:
            conn.executemany(sql, parametros)
            conn.commit()

    def buscar(self, id) -> Optional[dict]:
        """Retorna um registro pelo PK ou None."""
        sql = f"SELECT * FROM {self._tabela} WHERE {self._pk} = ?"
        with get_connection() as conn:
            row = conn.execute(sql, (id,)).fetchone()
        return self._parse_row(row) if row else None

    def listar(self) -> list[dict]:
        """Retorna todos os registros da tabela."""
        sql = f"SELECT * FROM {self._tabela}"
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [self._parse_row(r) for r in rows]

    def deletar(self, id) -> bool:
        """Remove um registro pelo PK. Retorna True se deletado."""
        sql = f"DELETE FROM {self._tabela} WHERE {self._pk} = ?"
        with get_connection() as conn:
            cur = conn.execute(sql, (id,))
            conn.commit()
            return cur.rowcount > 0

    def existe(self, id) -> bool:
        """Verifica se o registro existe."""
        sql = f"SELECT 1 FROM {self._tabela} WHERE {self._pk} = ?"
        with get_connection() as conn:
            row = conn.execute(sql, (id,)).fetchone()
        return row is not None

    def total(self) -> int:
        """Retorna a contagem total de registros."""
        sql = f"SELECT COUNT(*) FROM {self._tabela}"
        with get_connection() as conn:
            return conn.execute(sql).fetchone()[0]

    def filtrar(self, campo: str, valor) -> list[dict]:
        """Filtra registros por um campo e valor (igualdade)."""
        sql = f"SELECT * FROM {self._tabela} WHERE {campo} = ?"
        with get_connection() as conn:
            rows = conn.execute(sql, (valor,)).fetchall()
        return [self._parse_row(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Métodos extras
    # ------------------------------------------------------------------ #

    def filtrar_multiplos(self, filtros: dict) -> list[dict]:
        """Filtra com múltiplas condições AND (campo=valor)."""
        if not filtros:
            return self.listar()
        clausulas = " AND ".join(f"{c} = ?" for c in filtros)
        sql = f"SELECT * FROM {self._tabela} WHERE {clausulas}"
        with get_connection() as conn:
            rows = conn.execute(sql, list(filtros.values())).fetchall()
        return [self._parse_row(r) for r in rows]

    def buscar_por_campo(self, campo: str, valor) -> Optional[dict]:
        """Retorna o primeiro registro onde campo = valor."""
        sql = f"SELECT * FROM {self._tabela} WHERE {campo} = ? LIMIT 1"
        with get_connection() as conn:
            row = conn.execute(sql, (valor,)).fetchone()
        return self._parse_row(row) if row else None

    def executar_query(self, sql: str, params: tuple = ()) -> list[dict]:
        """Executa uma query customizada e retorna lista de dicts."""
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._parse_row(r) for r in rows]
