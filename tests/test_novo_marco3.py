import pytest
from services.indicador_service import IndicadorService
from models.aluno import Aluno
from api.validators import RegistroAcademicoSchema
from pydantic import ValidationError

def test_calculo_risco_desvio_padrao():
    aluno = Aluno(id="1", nome="Teste", matricula="001", curso="SI", periodo=1)
    aluno.adicionar_nota("Mat", 5.0, 1)
    aluno.adicionar_nota("Fis", 10.0, 1)
    aluno.adicionar_frequencia("Mat", 80.0, 1)

    # Mocking Repositorio
    class RepoMock: pass

    svc = IndicadorService(RepoMock())
    desvio = svc.calcular_desvio_padrao(aluno, 1)

    # Desvio de [5, 10] -> média 7.5 -> var(2.5^2 + 2.5^2)/1 = 12.5 -> sqrt(12.5) ~ 3.535...
    assert round(desvio, 2) == 3.54

def test_pydantic_validators():
    # Pass case
    schema = RegistroAcademicoSchema(cod_turma=101, nota_final=10.0, freq_presenca=100, ano=2023, semestre=1)
    assert schema.nota_final == 10.0

    # Fail nota > 10
    with pytest.raises(ValidationError):
        RegistroAcademicoSchema(cod_turma=101, nota_final=101.0, freq_presenca=100, ano=2023, semestre=1)

    # Fail nota < 0
    with pytest.raises(ValidationError):
        RegistroAcademicoSchema(cod_turma=101, nota_final=-1.0, freq_presenca=100, ano=2023, semestre=1)

    # Fail freq > 100
    with pytest.raises(ValidationError):
        RegistroAcademicoSchema(cod_turma=101, nota_final=5.0, freq_presenca=105, ano=2023, semestre=1)
