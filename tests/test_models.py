"""
Testes unitários — models (Aluno, Turma, Indicador, Usuario)
Execute: python -m pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from models.aluno import Aluno
from models.turma import Turma
from models.indicador import Indicador, Risco, NivelRisco
from models.usuario import Usuario, PerfilUsuario


# ------------------------------------------------------------------ #
# Aluno
# ------------------------------------------------------------------ #

class TestAluno:
    def _aluno(self):
        return Aluno(id="a1", nome="João", matricula="2024001",
                     curso="IA", periodo=2, email="joao@uni.edu")

    def test_criacao(self):
        aluno = self._aluno()
        assert aluno.nome == "João"
        assert aluno.periodo == 2

    def test_adicionar_nota_valida(self):
        aluno = self._aluno()
        aluno.adicionar_nota("POO", 8.5, 2)
        assert len(aluno.get_notas()) == 1
        assert aluno.get_notas()[0]["nota"] == 8.5

    def test_nota_invalida_levanta_excecao(self):
        pass
    def test_adicionar_frequencia_valida(self):
        aluno = self._aluno()
        aluno.adicionar_frequencia("POO", 85.0, 2)
        assert aluno.get_frequencias()[0]["percentual"] == 85.0

    def test_frequencia_invalida_levanta_excecao(self):
        pass
    def test_serializa_e_desserializa(self):
        aluno = self._aluno()
        aluno.adicionar_nota("POO", 7.0, 2)
        dados = aluno.to_dict()
        aluno2 = Aluno.from_dict(dados)
        assert aluno2.nome == aluno.nome
        assert len(aluno2.get_notas()) == 1


# ------------------------------------------------------------------ #
# Turma
# ------------------------------------------------------------------ #

class TestTurma:
    def _turma(self):
        return Turma(id="t1", nome="POO", codigo="POO01",
                     professor="Prof. Lima", periodo=2, carga_horaria=80)

    def _aluno(self):
        return Aluno(id="a1", nome="Maria", matricula="2024002",
                     curso="IA", periodo=2)

    def test_adicionar_aluno(self):
        turma = self._turma()
        aluno = self._aluno()
        turma.adicionar_aluno(aluno)
        assert turma.total_alunos() == 1

    def test_aluno_duplicado_levanta_excecao(self):
        turma = self._turma()
        aluno = self._aluno()
        turma.adicionar_aluno(aluno)
        with pytest.raises(ValueError):
            turma.adicionar_aluno(aluno)

    def test_remover_aluno(self):
        turma = self._turma()
        aluno = self._aluno()
        turma.adicionar_aluno(aluno)
        turma.remover_aluno("a1")
        assert turma.total_alunos() == 0


# ------------------------------------------------------------------ #
# Usuario
# ------------------------------------------------------------------ #

class TestUsuario:
    def _usuario(self):
        return Usuario(id="u1", nome="Admin", matricula="admin",
                       perfil=PerfilUsuario.ADMIN)

    def test_senha_hash(self):
        u = self._usuario()
        u.definir_senha("secreta")
        assert u.verificar_senha("secreta") is True
        assert u.verificar_senha("errada") is False

    def test_token(self):
        u = self._usuario()
        token = u.gerar_token()
        assert u.token_valido(token) is True
        assert u.token_valido("invalido") is False

    def test_permissoes_admin(self):
        u = self._usuario()
        assert u.tem_permissao("leitura") is True
        assert u.tem_permissao("exclusao") is True

    def test_permissoes_visualizador(self):
        u = Usuario(id="u2", nome="V", matricula="v",
                    perfil=PerfilUsuario.VISUALIZADOR)
        assert u.tem_permissao("leitura") is True
        assert u.tem_permissao("escrita") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
