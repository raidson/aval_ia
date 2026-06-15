import pytest
from services.indicador_service import IndicadorService


def test_calcular_iaa():
    """
    1. Teste a função do IAA: Passando média=8.0 e frequência=80.
    O resultado esperado (assert) deve ser exatamente (8.0 * 0.7) + (8.0 * 0.3) = 8.0.
    """
    media = 8.0
    frequencia = 80.0
    res = IndicadorService.calcular_iaa(media, frequencia)
    assert res == 8.0


def test_calcular_nota_efetiva():
    """
    2. Teste a Nota Efetiva: Passando média=10.0 e frequência=50.
    O resultado deve ser exatamente 5.0.
    """
    media = 10.0
    frequencia = 50.0
    res = IndicadorService.calcular_nota_efetiva(media, frequencia)
    assert res == 5.0


def test_calcular_tendencia_regressao():
    """
    3. Teste a Regressão Linear Simples: Passe uma lista de médias de queda brusca (ex: 9.0, 6.0, 3.0).
    O assert deve esperar a string "Decrescente".
    """
    medias = [9.0, 6.0, 3.0]
    res = IndicadorService.calcular_tendencia(medias)
    assert res == "Decrescente"


def test_classificacao_risco_critico():
    """
    4. Teste Classificação de Risco: Passe dados forçando um aluno com 2 evidências e média 2.5,
    validando se o retorno é "CRÍTICO".
    """
    # Média = 2.5 (< 5.0 -> 1ª evidência)
    # Frequência = 70.0 (< 75.0 -> 2ª evidência)
    # CV = 0.0
    risco, evidencias = IndicadorService.classificar_risco(2.5, 70.0, 0.0)
    assert risco == "CRÍTICO"
    assert len(evidencias) >= 2


def test_edge_cases():
    """
    5. Teste Edge Cases: Passe listas vazias para o Desvio Padrão e o CV e
    valide se o serviço não quebra (ZeroDivisionError), retornando 0.0.
    """
    res_dp = IndicadorService.calcular_desvio_padrao([])
    res_cv = IndicadorService.calcular_coeficiente_variacao([])
    assert res_dp == 0.0
    assert res_cv == 0.0

    # Testando com lista contendo apenas 1 elemento (também deve retornar 0.0)
    res_dp_1 = IndicadorService.calcular_desvio_padrao([5.0])
    res_cv_1 = IndicadorService.calcular_coeficiente_variacao([5.0])
    assert res_dp_1 == 0.0
    assert res_cv_1 == 0.0
