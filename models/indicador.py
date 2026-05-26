"""
Módulo: models/indicador.py
Representa um indicador acadêmico calculado para um aluno.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class NivelRisco(Enum):
    """Classificação do nível de risco acadêmico."""
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"
    CRITICO = "critico"


@dataclass
class Indicador:
    """Métrica calculada que resume o desempenho acadêmico de um aluno."""

    id: str
    aluno_id: str
    tipo: str                       # ex: "media_geral", "frequencia_media", "risco"
    valor: float
    descricao: str
    periodo: int
    gerado_em: str = ""

    def __post_init__(self):
        if not self.gerado_em:
            self.gerado_em = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "aluno_id": self.aluno_id,
            "tipo": self.tipo,
            "valor": self.valor,
            "descricao": self.descricao,
            "periodo": self.periodo,
            "gerado_em": self.gerado_em,
        }

    @classmethod
    def from_dict(cls, dados: dict) -> "Indicador":
        return cls(**dados)

    def __repr__(self) -> str:
        return f"Indicador(tipo={self.tipo!r}, valor={self.valor}, aluno={self.aluno_id!r})"


@dataclass
class Risco:
    """Representa a classificação de risco acadêmico de um aluno."""

    aluno_id: str
    nivel: NivelRisco
    justificativa: str
    evidencias: list
    gerado_em: str = ""

    def __post_init__(self):
        if not self.gerado_em:
            self.gerado_em = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "aluno_id": self.aluno_id,
            "nivel": self.nivel.value,
            "justificativa": self.justificativa,
            "evidencias": self.evidencias,
            "gerado_em": self.gerado_em,
        }
