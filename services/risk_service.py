import statistics

class RiskService:
    @staticmethod
    def pre_processar_notas(notas: list) -> list:
        """
        Substitui valores None/ausentes pela média das notas válidas (Null Imputation).
        Isso mantém a estabilidade estatística em cálculos de regressão linear.
        """
        notas_validas = [n for n in notas if n is not None]
        if not notas_validas:
            return [0.0 for _ in notas] # Se não há notas válidas, não podemos calcular média, retornamos 0

        media_validas = statistics.mean(notas_validas)
        return [float(n) if n is not None else float(media_validas) for n in notas]

    @staticmethod
    def pre_processar_frequencias(frequencias: list) -> list:
        """
        Substitui valores None/ausentes na frequência por 0 (indicando provável evasão/ausência total).
        """
        return [int(f) if f is not None else 0 for f in frequencias]
