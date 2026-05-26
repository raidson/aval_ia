"""
Módulo: services/aluno_service.py
Regras de negócio relacionadas a alunos.
"""

import uuid
from models.aluno import Aluno
from services.repositorio import Repositorio


class AlunoService:
    """Gerencia operações sobre alunos."""

    def __init__(self, repositorio: Repositorio):
        self._repo = repositorio

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #

    def cadastrar(self, nome: str, matricula: str, curso: str,
                  periodo: int, email: str = None) -> Aluno:
        """Cadastra um novo aluno no sistema."""
        if self._matricula_existe(matricula):
            raise ValueError(f"Matrícula {matricula} já cadastrada.")

        aluno = Aluno(
            id=str(uuid.uuid4()),
            nome=nome,
            matricula=matricula,
            curso=curso,
            periodo=periodo,
            email=email,
        )
        self._repo.salvar(aluno.id, aluno.to_dict())
        return aluno

    def buscar_por_id(self, aluno_id: str) -> Aluno:
        """Busca um aluno pelo ID. Lança exceção se não encontrado."""
        dados = self._repo.buscar(aluno_id)
        if not dados:
            raise ValueError(f"Aluno com ID {aluno_id!r} não encontrado.")
        return Aluno.from_dict(dados)

    def buscar_por_matricula(self, matricula: str) -> Aluno:
        """Busca um aluno pela matrícula."""
        resultados = self._repo.filtrar("matricula", matricula)
        if not resultados:
            raise ValueError(f"Matrícula {matricula!r} não encontrada.")
        return Aluno.from_dict(resultados[0])

    def listar_todos(self) -> list[Aluno]:
        """Retorna todos os alunos cadastrados."""
        return [Aluno.from_dict(d) for d in self._repo.listar()]

    def listar_por_periodo(self, periodo: int) -> list[Aluno]:
        """Filtra alunos por período."""
        return [Aluno.from_dict(d) for d in self._repo.filtrar("periodo", periodo)]

    def atualizar(self, aluno_id: str, **campos) -> Aluno:
        """Atualiza campos de um aluno existente."""
        aluno = self.buscar_por_id(aluno_id)
        dados = aluno.to_dict()
        campos_permitidos = {"nome", "email", "periodo", "curso"}
        for campo, valor in campos.items():
            if campo in campos_permitidos:
                dados[campo] = valor
        self._repo.salvar(aluno_id, dados)
        return Aluno.from_dict(dados)

    def remover(self, aluno_id: str) -> bool:
        """Remove um aluno do sistema."""
        if not self._repo.existe(aluno_id):
            raise ValueError(f"Aluno com ID {aluno_id!r} não encontrado.")
        return self._repo.deletar(aluno_id)

    # ------------------------------------------------------------------ #
    # Notas e frequências
    # ------------------------------------------------------------------ #

    def registrar_nota(self, aluno_id: str, disciplina: str,
                       nota: float, periodo: int) -> Aluno:
        """Registra uma nota para um aluno e persiste."""
        aluno = self.buscar_por_id(aluno_id)
        aluno.adicionar_nota(disciplina, nota, periodo)
        self._repo.salvar(aluno_id, aluno.to_dict())
        return aluno

    def registrar_frequencia(self, aluno_id: str, disciplina: str,
                              percentual: float, periodo: int) -> Aluno:
        """Registra a frequência de um aluno e persiste."""
        aluno = self.buscar_por_id(aluno_id)
        aluno.adicionar_frequencia(disciplina, percentual, periodo)
        self._repo.salvar(aluno_id, aluno.to_dict())
        return aluno

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _matricula_existe(self, matricula: str) -> bool:
        return len(self._repo.filtrar("matricula", matricula)) > 0
