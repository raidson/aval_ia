from pydantic import BaseModel, Field, field_validator
from typing import Optional

class AlunoImportSchema(BaseModel):
    nome_completo: str = Field(..., description="Nome do estudante")
    status_aluno: str = Field(..., description="Status do aluno")
    curso: Optional[str] = None
    matricula: Optional[str] = None
    periodo: Optional[int] = None
    email: Optional[str] = None

    @field_validator('status_aluno')
    def validate_status(cls, v):
        allowed = ['Ativo', 'Evadido', 'Formado']
        if v not in allowed:
            raise ValueError(f"Status '{v}' é inválido. Permitidos: {allowed}")
        return v

class RegistroAcademicoSchema(BaseModel):
    cod_turma: int = Field(..., description="Código da Turma")
    nota_final: float = Field(0.0, description="Nota final (0.0 a 100.0)")
    freq_presenca: int = Field(0, description="Frequência (0 a 100 inteiro)")
    ano: int = Field(..., description="Ano do registro")
    semestre: int = Field(..., description="Semestre do registro")

    @field_validator('nota_final')
    def validate_nota(cls, v):
        if not (0.0 <= v <= 100.0):
            raise ValueError("A nota deve estar entre 0.0 e 100.0")
        return v

    @field_validator('freq_presenca')
    def validate_freq(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("A frequência deve estar entre 0 e 100")
        return v

class TurmaSchema(BaseModel):
    cod_turma: int = Field(..., description="Código da Turma")
    nome_disciplina: str = Field(..., description="Nome da Disciplina")
