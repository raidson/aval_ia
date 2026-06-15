"""
Módulo: models/aluno.py
Entidade central do Nexus — representa um estudante com seu histórico acadêmico.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Aluno:
    """Representa um estudante cadastrado no sistema."""

    id: str
    nome: str
    matricula: str
    curso: str
    periodo: int
    email: Optional[str] = None
    _notas: list = field(default_factory=list, repr=False)
    _frequencias: list = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------ #
    # Notas
    # ------------------------------------------------------------------ #

    def adicionar_nota(self, disciplina: str, nota: float, periodo: int) -> None:
        """Registra uma nota para o aluno em uma disciplina."""
        from services.validation_service import ValidationService
        nota_validada = ValidationService.validar_nota(nota)
        self._notas.append({
            "disciplina": disciplina,
            "nota": nota_validada,
            "periodo": periodo
        })

    def get_notas(self) -> list:
        """Retorna todas as notas registradas."""
        return list(self._notas)

    def get_notas_por_disciplina(self, disciplina: str) -> list:
        """Retorna as notas de uma disciplina específica."""
        return [n for n in self._notas if n["disciplina"] == disciplina]

    # ------------------------------------------------------------------ #
    # Frequência
    # ------------------------------------------------------------------ #

    def adicionar_frequencia(self, disciplina: str, percentual: float, periodo: int) -> None:
        """Registra o percentual de frequência em uma disciplina."""
        from services.validation_service import ValidationService
        freq_validada = ValidationService.validar_frequencia(percentual)
        self._frequencias.append({
            "disciplina": disciplina,
            "percentual": freq_validada,
            "periodo": periodo
        })

    def get_frequencias(self) -> list:
        """Retorna todas as frequências registradas."""
        return list(self._frequencias)

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        """Converte o aluno para dicionário (útil para API/JSON)."""
        return {
            "id": self.id,
            "nome": self.nome,
            "matricula": self.matricula,
            "curso": self.curso,
            "periodo": self.periodo,
            "email": self.email,
            "notas": self._notas,
            "frequencias": self._frequencias,
        }

    @classmethod
    def from_dict(cls, dados: dict) -> "Aluno":
        """Cria um Aluno a partir de um dicionário."""
        aluno = cls(
            id=dados["id"],
            nome=dados["nome"],
            matricula=dados["matricula"],
            curso=dados["curso"],
            periodo=dados["periodo"],
            email=dados.get("email"),
        )
        for n in dados.get("notas", []):
            aluno._notas.append(n)
        for f in dados.get("frequencias", []):
            aluno._frequencias.append(f)
        return aluno

    def __repr__(self) -> str:
        return f"Aluno(matricula={self.matricula!r}, nome={self.nome!r}, periodo={self.periodo})"
