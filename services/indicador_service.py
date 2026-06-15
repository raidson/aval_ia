"""
Módulo: services/indicador_service.py
Motor de análise estatística — calcula indicadores e classifica risco acadêmico.
"""

import uuid
import math
import statistics
from typing import Union
from models.aluno import Aluno
from models.indicador import Indicador, Risco, NivelRisco
from services.risk_service import RiskService
from services.repositorio import Repositorio


class IndicadorService:
    """Gera e gerencia indicadores acadêmicos."""

    FREQUENCIA_MINIMA = 75.0
    NOTA_MINIMA = 5.0

    def __init__(self, repositorio: Repositorio):
        self._repo = repositorio

    # ------------------------------------------------------------------ #
    # Estatísticas individuais (Métodos de Cálculo Básicos)
    # ------------------------------------------------------------------ #

    @staticmethod
    def calcular_media(notas: list[float]) -> float:
        """
        Calcula a média aritmética de uma lista de notas.

        Args:
            notas (list[float]): Lista contendo as notas (0 a 10).

        Returns:
            float: A média aritmética arredondada para 2 casas decimais, ou 0.0 se a lista estiver vazia.
        """
        if not notas:
            return 0.0
        try:
            return round(statistics.mean(notas), 2)
        except Exception:
            return 0.0

    @staticmethod
    def calcular_media_geral(*args, **kwargs) -> float:
        """
        Calcula a média geral do aluno no período ou de uma lista de notas.

        Suporta duas assinaturas:
        1. calcular_media_geral(notas: list[float]) -> float
        2. calcular_media_geral(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: Média calculada.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            notas = [n.get("nota") for n in aluno.get_notas() if n.get("periodo") == periodo]
            notas_processadas = RiskService.pre_processar_notas(notas)
            if not notas_processadas:
                return 0.0
            return round(statistics.mean(notas_processadas), 2)

        notas = args[0] if len(args) > 0 else kwargs.get("notas", [])
        return IndicadorService.calcular_media(notas)

    @staticmethod
    def calcular_mediana(*args, **kwargs) -> float:
        """
        Calcula a mediana de uma lista de notas ou das notas do aluno no período.

        Suporta duas assinaturas:
        1. calcular_mediana(notas: list[float]) -> float
        2. calcular_mediana(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: Mediana calculada.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
            if not notas:
                return 0.0
            return round(statistics.median(notas), 2)

        notas = args[0] if len(args) > 0 else kwargs.get("notas", [])
        if not notas:
            return 0.0
        try:
            return round(statistics.median(notas), 2)
        except Exception:
            return 0.0

    @staticmethod
    def calcular_frequencia_media(*args, **kwargs) -> float:
        """
        Calcula a média de frequência de uma lista ou para um aluno no período.

        Suporta duas assinaturas:
        1. calcular_frequencia_media(frequencias: list[float]) -> float
        2. calcular_frequencia_media(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: Frequência média.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            freqs = [f.get("percentual") for f in aluno.get_frequencias() if f["periodo"] == periodo]
            freqs_processadas = RiskService.pre_processar_frequencias(freqs)
            if not freqs_processadas:
                return 0.0
            return round(statistics.mean(freqs_processadas), 2)

        freqs = args[0] if len(args) > 0 else kwargs.get("frequencias", [])
        if not freqs:
            return 0.0
        try:
            return round(statistics.mean(freqs), 2)
        except Exception:
            return 0.0

    @staticmethod
    def calcular_desvio_padrao(*args, **kwargs) -> float:
        """
        Calcula o desvio padrão amostral de uma lista ou das notas do aluno no período.

        Suporta duas assinaturas:
        1. calcular_desvio_padrao(notas: list[float]) -> float
        2. calcular_desvio_padrao(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: Desvio padrão amostral. Retorna 0.0 se a lista tiver menos de 2 elementos.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
            if len(notas) < 2:
                return 0.0
            return round(statistics.stdev(notas), 2)

        notas = args[0] if len(args) > 0 else kwargs.get("notas", [])
        if len(notas) < 2:
            return 0.0
        try:
            return round(statistics.stdev(notas), 2)
        except Exception:
            return 0.0

    @staticmethod
    def calcular_coeficiente_variacao(*args, **kwargs) -> float:
        """
        Calcula o coeficiente de variação em percentual ((desvio_padrao / media) * 100).

        Suporta duas assinaturas:
        1. calcular_coeficiente_variacao(notas: list[float]) -> float
        2. calcular_coeficiente_variacao(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: Coeficiente de variação. Retorna 0.0 em caso de divisão por zero.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            media = IndicadorService.calcular_media_geral(aluno, periodo)
            desvio = IndicadorService.calcular_desvio_padrao(aluno, periodo)
            if media == 0.0:
                return 0.0
            return round((desvio / media) * 100, 2)

        notas = args[0] if len(args) > 0 else kwargs.get("notas", [])
        if not notas:
            return 0.0
        try:
            media = IndicadorService.calcular_media(notas)
            if media == 0.0:
                return 0.0
            desvio = IndicadorService.calcular_desvio_padrao(notas)
            return round((desvio / media) * 100, 2)
        except ZeroDivisionError:
            return 0.0
        except Exception:
            return 0.0

    @staticmethod
    def calcular_notas_extremas(aluno: Aluno, periodo: int) -> dict[str, float]:
        """Retorna nota mínima e máxima no período."""
        notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
        if not notas:
            return {"min": 0.0, "max": 0.0}
        return {"min": round(min(notas), 2), "max": round(max(notas), 2)}

    def calcular_notas_por_disciplina(self, aluno: Aluno, periodo: int) -> dict[str, float]:
        """Retorna um dicionário {disciplina: nota} para o período."""
        return {
            n["disciplina"]: n["nota"]
            for n in aluno.get_notas()
            if n["periodo"] == periodo
        }

    @staticmethod
    def calcular_amplitude(*args, **kwargs) -> float:
        """
        Calcula a amplitude (nota_max - nota_min).

        Suporta duas assinaturas:
        1. calcular_amplitude(notas: list[float]) -> float
        2. calcular_amplitude(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: Amplitude das notas.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
            if not notas:
                return 0.0
            return round(max(notas) - min(notas), 2)

        notas = args[0] if len(args) > 0 else kwargs.get("notas", [])
        if not notas:
            return 0.0
        try:
            return round(max(notas) - min(notas), 2)
        except Exception:
            return 0.0

    @staticmethod
    def calcular_quartis(*args, **kwargs) -> dict[str, float]:
        """
        Calcula os quartis (Q1, Q3, IQR) usando statistics.quantiles.

        Suporta duas assinaturas:
        1. calcular_quartis(notas: list[float]) -> dict[str, float]
        2. calcular_quartis(aluno: Aluno, periodo: int) -> dict[str, float] (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            dict[str, float]: Dicionário contendo q1, q3 e iqr. A versão Aluno também contém q2.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            notas = sorted([n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo])
            n = len(notas)
            if n == 0:
                return {"q1": 0.0, "q2": 0.0, "q3": 0.0, "iqr": 0.0}
            if n < 4:
                med = round(statistics.median(notas), 2)
                return {"q1": round(notas[0], 2), "q2": med, "q3": round(notas[-1], 2),
                        "iqr": round(notas[-1] - notas[0], 2)}
            qs = statistics.quantiles(notas, n=4)
            q1, q2, q3 = round(qs[0], 2), round(qs[1], 2), round(qs[2], 2)
            return {"q1": q1, "q2": q2, "q3": q3, "iqr": round(q3 - q1, 2)}

        notas = args[0] if len(args) > 0 else kwargs.get("notas", [])
        if not notas:
            return {"q1": 0.0, "q3": 0.0, "iqr": 0.0}
        try:
            sorted_notas = sorted(notas)
            n = len(sorted_notas)
            if n < 4:
                q1 = sorted_notas[0]
                q3 = sorted_notas[-1]
                return {
                    "q1": round(float(q1), 2),
                    "q3": round(float(q3), 2),
                    "iqr": round(float(q3 - q1), 2)
                }
            qs = statistics.quantiles(sorted_notas, n=4)
            q1, q3 = round(qs[0], 2), round(qs[2], 2)
            return {
                "q1": q1,
                "q3": q3,
                "iqr": round(q3 - q1, 2)
            }
        except Exception:
            return {"q1": 0.0, "q3": 0.0, "iqr": 0.0}

    @staticmethod
    def calcular_assimetria(aluno: Aluno, periodo: int) -> float:
        """Assimetria amostral (Fisher): > 0 cauda direita, < 0 cauda esquerda."""
        notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
        n = len(notas)
        if n < 3:
            return 0.0
        media = statistics.mean(notas)
        desvio = statistics.stdev(notas)
        if desvio == 0:
            return 0.0
        soma = sum(((x - media) / desvio) ** 3 for x in notas)
        return round((n / ((n - 1) * (n - 2))) * soma, 3)

    @staticmethod
    def calcular_curtose(aluno: Aluno, periodo: int) -> float:
        """Curtose em excesso (Fisher): > 0 leptocúrtica, < 0 platicúrtica."""
        notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
        n = len(notas)
        if n < 4:
            return 0.0
        media = statistics.mean(notas)
        desvio = statistics.stdev(notas)
        if desvio == 0:
            return 0.0
        soma = sum(((x - media) / desvio) ** 4 for x in notas)
        kurt = ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * soma
        kurt -= (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))
        return round(kurt, 3)

    @staticmethod
    def calcular_zscore(*args, **kwargs) -> float:
        """
        Calcula o Z-Score.
        Fórmula: (media_aluno - media_turma) / desvio_padrao_turma

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: O valor do Z-Score arredondado, ou 0.0 se desvio_padrao_turma for 0.0.
        """
        if len(args) >= 3:
            media_aluno = args[0]
            media_turma = args[1]
            desvio_padrao_turma = args[2]
        else:
            media_aluno = kwargs.get("media_aluno", 0.0)
            media_turma = kwargs.get("media_turma", 0.0)
            desvio_padrao_turma = kwargs.get("desvio_padrao_turma", 0.0)

        if desvio_padrao_turma == 0.0:
            return 0.0
        try:
            return round((media_aluno - media_turma) / desvio_padrao_turma, 4)
        except Exception:
            return 0.0

    # ------------------------------------------------------------------ #
    # Indicadores Avançados e Exclusivos (Nível 2)
    # ------------------------------------------------------------------ #

    @staticmethod
    def calcular_iaa(*args, **kwargs) -> float:
        """
        Calcula o IAA (Índice de Aproveitamento Acadêmico).
        Composto com 70% de peso para a média e 30% para a frequência normalizada.
        Fórmula obrigatória: (media * 0.7) + ((frequencia / 10) * 0.3)

        Suporta duas assinaturas:
        1. calcular_iaa(media: float, frequencia: float) -> float
        2. calcular_iaa(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: O IAA calculado e arredondado para 2 casas decimais.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            media = IndicadorService.calcular_media_geral(aluno, periodo)
            freq = IndicadorService.calcular_frequencia_media(aluno, periodo)
            if media == 0:
                return 0.0
            return round((media * 0.7) + ((freq / 10.0) * 0.3), 2)

        media = args[0] if len(args) > 0 else kwargs.get("media", 0.0)
        frequencia = args[1] if len(args) > 1 else kwargs.get("frequencia", 0.0)
        try:
            return round((media * 0.7) + ((frequencia / 10.0) * 0.3), 2)
        except Exception:
            return 0.0

    @staticmethod
    def calcular_nota_efetiva(*args, **kwargs) -> float:
        """
        Calcula a Nota Efetiva.
        Penaliza a nota em relação à frequência.
        Fórmula obrigatória: media * (frequencia / 100)

        Suporta duas assinaturas:
        1. calcular_nota_efetiva(media: float, frequencia: float) -> float
        2. calcular_nota_efetiva(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: A Nota Efetiva arredondada para 2 casas decimais.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            media = IndicadorService.calcular_media_geral(aluno, periodo)
            freq = IndicadorService.calcular_frequencia_media(aluno, periodo)
            if media == 0:
                return 0.0
            return round(media * (freq / 100.0), 2)

        media = args[0] if len(args) > 0 else kwargs.get("media", 0.0)
        frequencia = args[1] if len(args) > 1 else kwargs.get("frequencia", 0.0)
        try:
            return round(media * (frequencia / 100.0), 2)
        except Exception:
            return 0.0

    @staticmethod
    def calcular_irp(*args, **kwargs) -> float:
        """
        Calcula o IRP (Índice de Risco Ponderado).
        Pontuação de 0 a 100 baseada em limites de penalidade.
        Peso de 40 para Nota, 40 para Frequência e 20 para Instabilidade (Coeficiente de Variação).

        Explicação da Lógica do IRP:
        - O IRP compõe uma pontuação de risco ponderando três fatores: nota do aluno (40 pts),
          assiduidade/frequência (40 pts) e instabilidade das notas representada pelo Coeficiente
          de Variação (20 pts).
        - Para Nota: se média < 5.0 (limite mínimo de aprovação), atribui a penalidade máxima (40 pts).
          Se média >= 7.0, a penalidade é 0. No intervalo [5.0, 7.0[, a penalidade varia linearmente.
        - Para Frequência: se frequência < 75% (limite mínimo legal), atribui a penalidade máxima (40 pts).
          Se frequência >= 85%, a penalidade é 0. No intervalo [75%, 85%[, a penalidade varia linearmente.
        - Para Instabilidade (CV): se CV > 40%, atribui a penalidade máxima (20 pts). Se CV <= 20%, a
          penalidade é 0. No intervalo ]20%, 40%], varia proporcionalmente.
        - O retorno é a soma dos três componentes de risco truncado em no máximo 100.0 e arredondado para
          1 casa decimal.

        Suporta duas assinaturas:
        1. calcular_irp(media: float, frequencia: float, coeficiente_variacao: float) -> float
        2. calcular_irp(aluno: Aluno, periodo: int) -> float (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            float: O IRP calculado e arredondado.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            media = IndicadorService.calcular_media_geral(aluno, periodo)
            freq = IndicadorService.calcular_frequencia_media(aluno, periodo)
            cv = IndicadorService.calcular_coeficiente_variacao(aluno, periodo)
        else:
            media = args[0] if len(args) > 0 else kwargs.get("media", 0.0)
            freq = args[1] if len(args) > 1 else kwargs.get("frequencia", 0.0)
            cv = args[2] if len(args) > 2 else kwargs.get("coeficiente_variacao", 0.0)

        try:
            # Componente nota (peso 40 pts)
            if media == 0:
                risco_nota = 20.0
            elif media < 5.0:  # NOTA_MINIMA
                risco_nota = 40.0
            elif media < 7.0:
                risco_nota = 20.0 * (7.0 - media) / 2.0
            else:
                risco_nota = 0.0

            # Componente frequência (peso 40 pts)
            if freq == 0:
                risco_freq = 20.0
            elif freq < 75.0:  # FREQUENCIA_MINIMA
                risco_freq = 40.0
            elif freq < 85.0:
                risco_freq = 20.0 * (85.0 - freq) / 10.0
            else:
                risco_freq = 0.0

            # Componente instabilidade / CV (peso 20 pts)
            if cv > 40.0:
                risco_cv = 20.0
            elif cv > 20.0:
                risco_cv = 20.0 * (cv - 20.0) / 20.0
            else:
                risco_cv = 0.0

            return round(min(100.0, risco_nota + risco_freq + risco_cv), 1)
        except Exception:
            return 0.0

    @staticmethod
    def calcular_tendencia(medias: list[float], periodos: list[float] = None) -> str:
        """
        Calcula a tendência entre períodos usando Regressão Linear Simples.
        Fórmula do slope: (n * sum(xy) - sum(x) * sum(y)) / (n * sum(x^2) - (sum(x))^2)

        Explicação da Lógica da Regressão Linear Simples:
        - A tendência avalia a evolução cronológica das notas de um aluno.
        - Usamos a fórmula clássica dos mínimos quadrados para calcular a inclinação (slope) da reta
          de regressão linear, onde 'medias' representa os valores observados no eixo y e 'periodos'
          representa a variável temporal no eixo x.
        - Se a inclinação for marcadamente positiva (slope > 0.3), a tendência é considerada "Crescente".
        - Se a inclinação for marcadamente negativa (slope < -0.3), a tendência é considerada "Decrescente".
        - Caso contrário, a evolução é classificada como "Estável".

        Args:
            medias (list[float]): Lista de médias cronológicas.
            periodos (list[float], opcional): Lista de períodos. Se omitida, assume-se [1, 2, ..., n].

        Returns:
            str: "Crescente", "Decrescente" ou "Estável".
        """
        n = len(medias)
        if n < 2:
            return "Estável"
        if periodos is None:
            periodos = list(range(1, n + 1))
        elif len(periodos) != n:
            return "Estável"

        try:
            soma_x = sum(periodos)
            soma_y = sum(medias)
            soma_xy = sum(x * y for x, y in zip(periodos, medias))
            soma_x2 = sum(x ** 2 for x in periodos)

            denom = (n * soma_x2) - (soma_x ** 2)
            if denom == 0:
                return "Estável"

            slope = ((n * soma_xy) - (soma_x * soma_y)) / denom

            if slope > 0.3:
                return "Crescente"
            elif slope < -0.3:
                return "Decrescente"
            else:
                return "Estável"
        except Exception:
            return "Estável"

    def calcular_tendencia_periodo(self, aluno: Aluno) -> dict:
        """Tendência de evolução entre períodos via regressão linear simples (Original)."""
        periodos = sorted(set(n["periodo"] for n in aluno.get_notas()))
        if len(periodos) < 2:
            medias = []
            if periodos:
                m = self.calcular_media_geral(aluno, periodos[0])
                medias = [m]
            return {"periodos": periodos, "medias": medias,
                    "tendencia": "sem_dados", "inclinacao": 0.0, "variacao": 0.0}

        medias = []
        for p in periodos:
            notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == p]
            medias.append(round(statistics.mean(notas), 2) if notas else 0.0)

        n = len(periodos)
        x = list(range(1, n + 1))
        soma_x  = sum(x)
        soma_y  = sum(medias)
        soma_xy = sum(x[i] * medias[i] for i in range(n))
        soma_x2 = sum(xi ** 2 for xi in x)
        denom = n * soma_x2 - soma_x ** 2
        slope = round((n * soma_xy - soma_x * soma_y) / denom, 3) if denom else 0.0

        variacao = round(medias[-1] - medias[0], 2)
        if slope > 0.3:
            tendencia = "crescente"
        elif slope < -0.3:
            tendencia = "decrescente"
        else:
            tendencia = "estavel"

        return {"periodos": periodos, "medias": medias,
                "tendencia": tendencia, "inclinacao": slope, "variacao": variacao}

    # ------------------------------------------------------------------ #
    # Análise comparativa com a turma
    # ------------------------------------------------------------------ #

    def calcular_zscore_aluno(self, alunos: list, aluno_id: str, periodo: int) -> float:
        """Z-score do aluno em relação à turma — quantos desvios acima/abaixo da média."""
        medias = {a.id: self.calcular_media_geral(a, periodo) for a in alunos}
        media_aluno = medias.get(aluno_id, 0.0)
        valores = [m for m in medias.values() if m > 0]
        if len(valores) < 2:
            return 0.0
        media_turma = statistics.mean(valores)
        desvio = statistics.stdev(valores)
        if desvio == 0:
            return 0.0
        return round((media_aluno - media_turma) / desvio, 4)

    def calcular_percentil_aluno(self, alunos: list, aluno_id: str, periodo: int) -> float:
        """Percentil do aluno dentro da turma (0–100)."""
        medias = [(a.id, self.calcular_media_geral(a, periodo)) for a in alunos]
        media_aluno = dict(medias).get(aluno_id, 0.0)
        valores = sorted([m for _, m in medias if m > 0])
        if not valores:
            return 0.0
        abaixo = sum(1 for v in valores if v < media_aluno)
        return round((abaixo / len(valores)) * 100, 1)

    # ------------------------------------------------------------------ #
    # Estatísticas da turma
    # ------------------------------------------------------------------ #

    def calcular_estatisticas_turma(self, alunos: list, periodo: int) -> dict:
        """Estatísticas descritivas da turma: média, mediana, desvio, CV, min, max."""
        medias = [self.calcular_media_geral(a, periodo) for a in alunos]
        freqs = [self.calcular_frequencia_media(a, periodo) for a in alunos]
        medias_validas = [m for m in medias if m > 0]
        freqs_validas = [f for f in freqs if f > 0]

        if not medias_validas:
            return {}

        media_inst = round(statistics.mean(medias_validas), 2)
        desvio = round(statistics.stdev(medias_validas), 2) if len(medias_validas) >= 2 else 0.0

        return {
            "media_institucional": media_inst,
            "mediana_institucional": round(statistics.median(medias_validas), 2),
            "desvio_padrao_turma": desvio,
            "coeficiente_variacao": round((desvio / media_inst) * 100, 2) if media_inst > 0 else 0.0,
            "nota_maxima_turma": round(max(medias_validas), 2),
            "nota_minima_turma": round(min(medias_validas), 2),
            "frequencia_media_turma": round(statistics.mean(freqs_validas), 2) if freqs_validas else 0.0,
            "total_alunos": len(alunos),
            "taxa_aprovacao": round(
                sum(1 for m in medias_validas if m >= self.NOTA_MINIMA) / len(medias_validas) * 100, 1
            ),
        }

    def calcular_correlacao_freq_nota(self, alunos: list, periodo: int) -> float:
        """Correlação de Pearson entre frequência média e nota média da turma."""
        pares = []
        for aluno in alunos:
            media = self.calcular_media_geral(aluno, periodo)
            freq = self.calcular_frequencia_media(aluno, periodo)
            if media > 0 and freq > 0:
                pares.append((freq, media))
        if len(pares) < 2:
            return 0.0
        n = len(pares)
        soma_x = sum(p[0] for p in pares)
        soma_y = sum(p[1] for p in pares)
        soma_xy = sum(p[0] * p[1] for p in pares)
        soma_x2 = sum(p[0] ** 2 for p in pares)
        soma_y2 = sum(p[1] ** 2 for p in pares)
        num = n * soma_xy - soma_x * soma_y
        den = math.sqrt(max(0, (n * soma_x2 - soma_x ** 2) * (n * soma_y2 - soma_y ** 2)))
        if den == 0:
            return 0.0
        return round(num / den, 4)

    def calcular_distribuicao_medias(self, alunos: list, periodo: int) -> dict:
        """Histograma de médias em faixas de 2 pontos."""
        faixas = {"0–2": 0, "2–4": 0, "4–6": 0, "6–8": 0, "8–10": 0}
        for aluno in alunos:
            media = self.calcular_media_geral(aluno, periodo)
            if media < 2:
                faixas["0–2"] += 1
            elif media < 4:
                faixas["2–4"] += 1
            elif media < 6:
                faixas["4–6"] += 1
            elif media < 8:
                faixas["6–8"] += 1
            else:
                faixas["8–10"] += 1
        return faixas

    def calcular_estatisticas_por_disciplina(self, alunos: list, periodo: int) -> list:
        """Estatísticas descritivas por disciplina: média, mediana, desvio, taxa de aprovação."""
        disciplinas: dict = {}
        for aluno in alunos:
            for nota in aluno.get_notas():
                if nota["periodo"] == periodo:
                    disc = nota["disciplina"]
                    disciplinas.setdefault(disc, {"notas": [], "frequencias": []})
                    disciplinas[disc]["notas"].append(nota["nota"])
            for freq in aluno.get_frequencias():
                if freq["periodo"] == periodo:
                    disc = freq["disciplina"]
                    disciplinas.setdefault(disc, {"notas": [], "frequencias": []})
                    disciplinas[disc]["frequencias"].append(freq["percentual"])

        resultado = []
        for disc, dados in sorted(disciplinas.items()):
            notas = dados["notas"]
            freqs = dados["frequencias"]
            if not notas:
                continue
            entry = {
                "disciplina": disc,
                "media": round(statistics.mean(notas), 2),
                "mediana": round(statistics.median(notas), 2),
                "desvio_padrao": round(statistics.stdev(notas), 2) if len(notas) >= 2 else 0.0,
                "nota_min": round(min(notas), 2),
                "nota_max": round(max(notas), 2),
                "total_alunos": len(notas),
                "taxa_aprovacao": round(
                    sum(1 for n in notas if n >= self.NOTA_MINIMA) / len(notas) * 100, 1
                ),
            }
            if freqs:
                entry["frequencia_media"] = round(statistics.mean(freqs), 2)
            resultado.append(entry)
        return resultado

    def calcular_pontos_dispersao(self, alunos: list, periodo: int) -> list:
        """Retorna lista de pontos {nome, frequencia, media} para scatter plot."""
        pontos = []
        for aluno in alunos:
            media = self.calcular_media_geral(aluno, periodo)
            freq = self.calcular_frequencia_media(aluno, periodo)
            if media > 0 or freq > 0:
                pontos.append({
                    "nome": aluno.nome,
                    "frequencia": freq,
                    "media": media,
                })
        return pontos

    # ------------------------------------------------------------------ #
    # Geração de indicadores persistidos
    # ------------------------------------------------------------------ #

    def gerar_indicadores_aluno(self, aluno: Aluno, periodo: int, salvar: bool = True) -> list[Indicador]:
        """Gera e persiste todos os indicadores do aluno no período."""
        indicadores = []

        calculos = [
            ("media_geral",          self.calcular_media_geral(aluno, periodo),
             f"Média aritmética das notas — período {periodo}"),
            ("mediana",              self.calcular_mediana(aluno, periodo),
             f"Mediana das notas — período {periodo}"),
            ("frequencia_media",     self.calcular_frequencia_media(aluno, periodo),
             f"Frequência média — período {periodo}"),
            ("desvio_padrao",        self.calcular_desvio_padrao(aluno, periodo),
             f"Desvio padrão das notas — período {periodo}"),
            ("coeficiente_variacao", self.calcular_coeficiente_variacao(aluno, periodo),
             f"Coeficiente de variação (%) — período {periodo}"),
            ("amplitude",            self.calcular_amplitude(aluno, periodo),
             f"Amplitude das notas (max−min) — período {periodo}"),
            ("iaa",                  self.calcular_iaa(aluno, periodo),
             f"Índice de Aproveitamento Acadêmico — período {periodo}"),
            ("nota_efetiva",         self.calcular_nota_efetiva(aluno, periodo),
             f"Nota efetiva ajustada pela frequência — período {periodo}"),
            ("irp",                  self.calcular_irp(aluno, periodo),
             f"Índice de Risco Ponderado (0–100) — período {periodo}"),
            ("assimetria",           self.calcular_assimetria(aluno, periodo),
             f"Assimetria amostral da distribuição de notas — período {periodo}"),
            ("curtose",              self.calcular_curtose(aluno, periodo),
             f"Curtose em excesso da distribuição de notas — período {periodo}"),
        ]

        for tipo, valor, descricao in calculos:
            ind = Indicador(
                id=str(uuid.uuid4()),
                aluno_id=aluno.id,
                tipo=tipo,
                valor=valor,
                descricao=descricao,
                periodo=periodo,
            )
            if salvar:
                self._repo.salvar(ind.id, ind.to_dict())
            indicadores.append(ind)

        return indicadores

    # ------------------------------------------------------------------ #
    # Classificação de Risco (Passo 3)
    # ------------------------------------------------------------------ #

    @staticmethod
    def classificar_risco(*args, **kwargs) -> Union[Risco, tuple[str, list[str]]]:
        """
        Classifica o risco acadêmico.

        Suporta duas assinaturas:
        1. classificar_risco(media: float, frequencia: float, coeficiente_variacao: float) -> tuple[str, list[str]]
        2. classificar_risco(aluno: Aluno, periodo: int) -> Risco (Compatibilidade)

        Args:
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            Risco ou tuple[str, list[str]]: Classificação de risco e evidências.
        """
        if args and isinstance(args[0], Aluno):
            aluno = args[0]
            periodo = args[1] if len(args) > 1 else 1
            media = IndicadorService.calcular_media_geral(aluno, periodo)
            freq = IndicadorService.calcular_frequencia_media(aluno, periodo)
            cv = IndicadorService.calcular_coeficiente_variacao(aluno, periodo)

            nivel_str, evidencias = IndicadorService.classificar_risco_valores(media, freq, cv)

            nivel_map = {
                "BAIXO": NivelRisco.BAIXO,
                "MÉDIO": NivelRisco.MEDIO,
                "ALTO": NivelRisco.ALTO,
                "CRÍTICO": NivelRisco.CRITICO
            }
            nivel_enum = nivel_map.get(nivel_str, NivelRisco.MEDIO)

            if nivel_str == "MÉDIO" and not evidencias:
                justificativa = "Sem dados suficientes para análise."
            elif nivel_str == "BAIXO":
                justificativa = "Aluno dentro dos parâmetros esperados."
            elif nivel_str == "MÉDIO":
                justificativa = "Um indicador abaixo do esperado."
            else:
                justificativa = "Múltiplos indicadores críticos detectados."

            return Risco(
                aluno_id=aluno.id,
                nivel=nivel_enum,
                justificativa=justificativa,
                evidencias=evidencias
            )

        media = args[0] if len(args) > 0 else kwargs.get("media", 0.0)
        frequencia = args[1] if len(args) > 1 else kwargs.get("frequencia", 0.0)
        coeficiente_variacao = args[2] if len(args) > 2 else kwargs.get("coeficiente_variacao", 0.0)

        return IndicadorService.classificar_risco_valores(media, frequencia, coeficiente_variacao)

    @staticmethod
    def classificar_risco_valores(media: float, frequencia: float, coeficiente_variacao: float) -> tuple[str, list[str]]:
        """
        Gera uma lista de strings chamadas 'evidências' sempre que os limiares de atenção forem rompidos.
        Com base na quantidade e gravidade dessas evidências, retorne uma string de risco e a lista.

        Regras estritas:
        - Se não houver dados (ambos zero): Retorne "MÉDIO" (sem dados suficientes).
        - Nenhuma evidência crítica: Retorne "BAIXO".
        - 1 evidência crítica: Retorne "MÉDIO".
        - 2 ou mais evidências, com média >= 3.0: Retorne "ALTO".
        - 2 ou mais evidências, com média < 3.0: Retorne "CRÍTICO".

        Args:
            media (float): Média das notas.
            frequencia (float): Percentual de frequência.
            coeficiente_variacao (float): Coeficiente de variação.

        Returns:
            tuple[str, list[str]]: O nível de risco ("BAIXO", "MÉDIO", "ALTO", "CRÍTICO") e a lista de evidências.
        """
        evidencias = []

        if media == 0.0 and frequencia == 0.0:
            return "MÉDIO", []

        if media < 5.0:
            evidencias.append(f"Média {media} abaixo do mínimo (5.0)")

        if frequencia < 75.0:
            evidencias.append(f"Frequência {frequencia}% abaixo do mínimo (75.0%)")

        if coeficiente_variacao > 40.0:
            evidencias.append(f"Alta instabilidade nas notas (CV={coeficiente_variacao}%)")

        n_evidencias = len(evidencias)

        if n_evidencias == 0:
            return "BAIXO", evidencias
        elif n_evidencias == 1:
            return "MÉDIO", evidencias
        else:
            if media >= 3.0:
                return "ALTO", evidencias
            else:
                return "CRÍTICO", evidencias

    def listar_indicadores_aluno(self, aluno_id: str) -> list[Indicador]:
        """Retorna todos os indicadores persistidos de um aluno."""
        dados = self._repo.filtrar("aluno_id", aluno_id)
        return [Indicador.from_dict(d) for d in dados]
