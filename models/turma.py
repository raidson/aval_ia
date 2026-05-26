"""
Módulo: models/turma.py
Representa uma turma/disciplina com seus alunos associados.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.aluno import Aluno


@dataclass
class Turma:
    """Representa uma disciplina/turma acadêmica."""

    id: str
    nome: str
    codigo: str
    professor: str
    periodo: int
    carga_horaria: int
    _alunos: list = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------ #
    # Gestão de alunos
    # ------------------------------------------------------------------ #

    def adicionar_aluno(self, aluno: "Aluno") -> None:
        """Matricula um aluno na turma."""
        ids_existentes = [a["id"] for a in self._alunos]
        if aluno.id in ids_existentes:
            raise ValueError(f"Aluno {aluno.matricula} já está matriculado nesta turma.")
        self._alunos.append({"id": aluno.id, "matricula": aluno.matricula, "nome": aluno.nome})

    def remover_aluno(self, aluno_id: str) -> None:
        """Remove um aluno da turma pelo ID."""
        self._alunos = [a for a in self._alunos if a["id"] != aluno_id]

    def get_alunos(self) -> list:
        """Retorna a lista de alunos matriculados."""
        return list(self._alunos)

    def total_alunos(self) -> int:
        """Retorna o número de alunos matriculados."""
        return len(self._alunos)

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "codigo": self.codigo,
            "professor": self.professor,
            "periodo": self.periodo,
            "carga_horaria": self.carga_horaria,
            "alunos": self._alunos,
        }

    @classmethod
    def from_dict(cls, dados: dict) -> "Turma":
        turma = cls(
            id=dados["id"],
            nome=dados["nome"],
            codigo=dados["codigo"],
            professor=dados["professor"],
            periodo=dados["periodo"],
            carga_horaria=dados["carga_horaria"],
        )
        turma._alunos = dados.get("alunos", [])
        return turma

    def __repr__(self) -> str:
        return f"Turma(codigo={self.codigo!r}, nome={self.nome!r}, alunos={self.total_alunos()})"
