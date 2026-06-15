"""
Módulo: services/indicador_service.py
Motor de análise estatística — calcula indicadores e classifica risco acadêmico.
"""

import uuid
import math
import statistics
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
    # Estatísticas individuais
    # ------------------------------------------------------------------ #

    def calcular_media_geral(self, aluno: Aluno, periodo: int) -> float:
        """Média aritmética das notas do aluno no período."""
        notas = [n.get("nota") for n in aluno.get_notas() if n.get("periodo") == periodo]
        notas_processadas = RiskService.pre_processar_notas(notas)
        if not notas_processadas:
            return 0.0
        return round(statistics.mean(notas_processadas), 2)
    def calcular_mediana(self, aluno: Aluno, periodo: int) -> float:
        """Mediana das notas do aluno no período."""
        notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
        if not notas:
            return 0.0
        return round(statistics.median(notas), 2)

    def calcular_frequencia_media(self, aluno: Aluno, periodo: int) -> float:
        """Média de frequência do aluno no período."""
        freqs = [f.get("percentual") for f in aluno.get_frequencias() if f["periodo"] == periodo]
        freqs_processadas = RiskService.pre_processar_frequencias(freqs)
        if not freqs_processadas:
            return 0.0
        return round(statistics.mean(freqs_processadas), 2)

    def calcular_desvio_padrao(self, aluno: Aluno, periodo: int) -> float:
        """Desvio padrão das notas — indicador de instabilidade."""
        notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
        if len(notas) < 2:
            return 0.0
        return round(statistics.stdev(notas), 2)

    def calcular_coeficiente_variacao(self, aluno: Aluno, periodo: int) -> float:
        """CV = (desvio_padrão / média) × 100 — dispersão relativa das notas."""
        media = self.calcular_media_geral(aluno, periodo)
        desvio = self.calcular_desvio_padrao(aluno, periodo)
        if media == 0:
            return 0.0
        return round((desvio / media) * 100, 2)

    def calcular_notas_extremas(self, aluno: Aluno, periodo: int) -> dict:
        """Retorna nota mínima e máxima no período."""
        notas = [n["nota"] for n in aluno.get_notas() if n["periodo"] == periodo]
        if not notas:
            return {"min": 0.0, "max": 0.0}
        return {"min": round(min(notas), 2), "max": round(max(notas), 2)}

    def calcular_notas_por_disciplina(self, aluno: Aluno, periodo: int) -> dict:
        """Retorna um dicionário {disciplina: nota} para o período."""
        return {
            n["disciplina"]: n["nota"]
            for n in aluno.get_notas()
            if n["periodo"] == periodo
        }

    def calcular_amplitude(self, aluno: Aluno, periodo: int) -> float:
        """Amplitude = nota_max − nota_min — medida de dispersão absoluta."""
        extremas = self.calcular_notas_extremas(aluno, periodo)
        return round(extremas["max"] - extremas["min"], 2)

    def calcular_quartis(self, aluno: Aluno, periodo: int) -> dict:
        """Quartis (Q1, Q2, Q3) e IQR para análise de dispersão e outliers."""
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

    def calcular_assimetria(self, aluno: Aluno, periodo: int) -> float:
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

    def calcular_curtose(self, aluno: Aluno, periodo: int) -> float:
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

    def calcular_iaa(self, aluno: Aluno, periodo: int) -> float:
        """IAA — Índice de Aproveitamento Acadêmico: nota (70%) + frequência normalizada (30%)."""
        media = self.calcular_media_geral(aluno, periodo)
        freq = self.calcular_frequencia_media(aluno, periodo)
        if media == 0:
            return 0.0
        return round(media * 0.7 + (freq / 10.0) * 0.3, 2)

    def calcular_nota_efetiva(self, aluno: Aluno, periodo: int) -> float:
        """Nota Efetiva — média penalizada pela frequência real do aluno."""
        media = self.calcular_media_geral(aluno, periodo)
        freq = self.calcular_frequencia_media(aluno, periodo)
        if media == 0:
            return 0.0
        return round(media * (freq / 100.0), 2)

    def calcular_irp(self, aluno: Aluno, periodo: int) -> float:
        """IRP — Índice de Risco Ponderado (0–100): quanto maior, mais crítico."""
        media = self.calcular_media_geral(aluno, periodo)
        freq  = self.calcular_frequencia_media(aluno, periodo)
        cv    = self.calcular_coeficiente_variacao(aluno, periodo)

        # Componente nota (peso 40 pts)
        if media == 0:
            risco_nota = 20.0
        elif media < self.NOTA_MINIMA:
            risco_nota = 40.0
        elif media < 7.0:
            risco_nota = 20.0 * (7.0 - media) / 2.0
        else:
            risco_nota = 0.0

        # Componente frequência (peso 40 pts)
        if freq == 0:
            risco_freq = 20.0
        elif freq < self.FREQUENCIA_MINIMA:
            risco_freq = 40.0
        elif freq < 85.0:
            risco_freq = 20.0 * (85.0 - freq) / 10.0
        else:
            risco_freq = 0.0

        # Componente instabilidade / CV (peso 20 pts)
        if cv > 40:
            risco_cv = 20.0
        elif cv > 20:
            risco_cv = 20.0 * (cv - 20) / 20.0
        else:
            risco_cv = 0.0

        return round(min(100.0, risco_nota + risco_freq + risco_cv), 1)

    def calcular_tendencia_periodo(self, aluno: Aluno) -> dict:
        """Tendência de evolução entre períodos via regressão linear simples."""
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

    def gerar_indicadores_aluno(self, aluno: Aluno, periodo: int, salvar: bool = True) -> list:
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
    # Classificação de risco
    # ------------------------------------------------------------------ #

    def classificar_risco(self, aluno: Aluno, periodo: int) -> Risco:
        """Classifica o risco acadêmico combinando nota, frequência e instabilidade."""
        media = self.calcular_media_geral(aluno, periodo)
        freq = self.calcular_frequencia_media(aluno, periodo)
        cv = self.calcular_coeficiente_variacao(aluno, periodo)
        evidencias = []

        if media > 0 and media < self.NOTA_MINIMA:
            evidencias.append(f"Média {media} abaixo do mínimo ({self.NOTA_MINIMA})")
        if freq > 0 and freq < self.FREQUENCIA_MINIMA:
            evidencias.append(f"Frequência {freq}% abaixo do mínimo ({self.FREQUENCIA_MINIMA}%)")
        if cv > 40:
            evidencias.append(f"Alta instabilidade nas notas (CV={cv}%)")

        if media == 0.0 and freq == 0.0:
            nivel = NivelRisco.MEDIO
            justificativa = "Sem dados suficientes para análise."
        elif len(evidencias) == 0:
            nivel = NivelRisco.BAIXO
            justificativa = "Aluno dentro dos parâmetros esperados."
        elif len(evidencias) == 1:
            nivel = NivelRisco.MEDIO
            justificativa = "Um indicador abaixo do esperado."
        else:
            nivel = NivelRisco.ALTO if media >= 3.0 else NivelRisco.CRITICO
            justificativa = "Múltiplos indicadores críticos detectados."

        return Risco(
            aluno_id=aluno.id,
            nivel=nivel,
            justificativa=justificativa,
            evidencias=evidencias,
        )

    def listar_indicadores_aluno(self, aluno_id: str) -> list:
        """Retorna todos os indicadores persistidos de um aluno."""
        dados = self._repo.filtrar("aluno_id", aluno_id)
        return [Indicador.from_dict(d) for d in dados]
