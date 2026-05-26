"""
Testes unitários — services (AlunoService, IndicadorService)
Execute: python -m pytest tests/ -v
"""

import sys, os, tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from models.indicador import NivelRisco
from services.repositorio import Repositorio
from services.aluno_service import AlunoService
from services.indicador_service import IndicadorService


def _repo_temp():
    """Cria um repositório temporário para testes isolados."""
    tmp = tempfile.mktemp(suffix=".json")
    return Repositorio(tmp)


# ------------------------------------------------------------------ #
# AlunoService
# ------------------------------------------------------------------ #

class TestAlunoService:
    def setup_method(self):
        self.service = AlunoService(_repo_temp())

    def test_cadastrar_aluno(self):
        aluno = self.service.cadastrar("João", "2024001", "IA", 2)
        assert aluno.nome == "João"
        assert aluno.matricula == "2024001"

    def test_matricula_duplicada_levanta_excecao(self):
        self.service.cadastrar("João", "2024001", "IA", 2)
        with pytest.raises(ValueError):
            self.service.cadastrar("João2", "2024001", "IA", 2)

    def test_buscar_por_id(self):
        aluno = self.service.cadastrar("Maria", "2024002", "IA", 2)
        encontrado = self.service.buscar_por_id(aluno.id)
        assert encontrado.nome == "Maria"

    def test_id_inexistente_levanta_excecao(self):
        with pytest.raises(ValueError):
            self.service.buscar_por_id("id-falso")

    def test_listar_todos(self):
        self.service.cadastrar("A", "001", "IA", 2)
        self.service.cadastrar("B", "002", "IA", 2)
        assert len(self.service.listar_todos()) == 2

    def test_registrar_nota(self):
        aluno = self.service.cadastrar("Pedro", "2024003", "IA", 2)
        aluno = self.service.registrar_nota(aluno.id, "POO", 9.0, 2)
        assert len(aluno.get_notas()) == 1

    def test_registrar_frequencia(self):
        aluno = self.service.cadastrar("Laura", "2024004", "IA", 2)
        aluno = self.service.registrar_frequencia(aluno.id, "POO", 88.0, 2)
        assert len(aluno.get_frequencias()) == 1


# ------------------------------------------------------------------ #
# IndicadorService
# ------------------------------------------------------------------ #

class TestIndicadorService:
    def setup_method(self):
        repo_alunos = _repo_temp()
        self.aluno_service = AlunoService(repo_alunos)
        self.indicador_service = IndicadorService(_repo_temp())

    def _criar_aluno_com_dados(self):
        aluno = self.aluno_service.cadastrar("Teste", "9999", "IA", 2)
        self.aluno_service.registrar_nota(aluno.id, "POO", 8.0, 2)
        self.aluno_service.registrar_nota(aluno.id, "Estatística", 6.0, 2)
        self.aluno_service.registrar_frequencia(aluno.id, "POO", 90.0, 2)
        self.aluno_service.registrar_frequencia(aluno.id, "Estatística", 80.0, 2)
        return self.aluno_service.buscar_por_id(aluno.id)

    def test_media_geral(self):
        aluno = self._criar_aluno_com_dados()
        media = self.indicador_service.calcular_media_geral(aluno, 2)
        assert media == 7.0

    def test_frequencia_media(self):
        aluno = self._criar_aluno_com_dados()
        freq = self.indicador_service.calcular_frequencia_media(aluno, 2)
        assert freq == 85.0

    def test_risco_baixo(self):
        aluno = self._criar_aluno_com_dados()
        risco = self.indicador_service.classificar_risco(aluno, 2)
        assert risco.nivel == NivelRisco.BAIXO

    def test_risco_alto_nota_baixa(self):
        aluno = self.aluno_service.cadastrar("Risco", "0001", "IA", 2)
        self.aluno_service.registrar_nota(aluno.id, "POO", 2.0, 2)
        self.aluno_service.registrar_frequencia(aluno.id, "POO", 50.0, 2)
        aluno = self.aluno_service.buscar_por_id(aluno.id)
        risco = self.indicador_service.classificar_risco(aluno, 2)
        assert risco.nivel in (NivelRisco.ALTO, NivelRisco.CRITICO)

    def test_gerar_indicadores(self):
        aluno = self._criar_aluno_com_dados()
        indicadores = self.indicador_service.gerar_indicadores_aluno(aluno, 2)
        tipos = {i.tipo for i in indicadores}
        assert "media_geral" in tipos
        assert "frequencia_media" in tipos
        assert "desvio_padrao" in tipos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
