class ValidationService:
    @staticmethod
    def validar_nota(nota) -> float:
        """
        Valida e converte a nota para float64 (Float do Python).
        Garante que a nota está entre 0.0 e 100.0.
        """
        if nota is None:
            raise ValueError("A nota não pode ser None")
        try:
            nota_float = float(nota)
        except (ValueError, TypeError):
            raise TypeError(f"A nota deve ser um valor numérico. Recebido: {type(nota)}")

        if not (0.0 <= nota_float <= 100.0):
            raise ValueError(f"Nota inválida: {nota_float}. Deve estar entre 0.0 e 100.0.")

        return nota_float

    @staticmethod
    def validar_frequencia(frequencia) -> int:
        """
        Valida e converte a frequência para inteiro.
        Garante que a frequência está entre 0 e 100.
        """
        if frequencia is None:
            raise ValueError("A frequência não pode ser None")
        try:
            # We explicitly cast to int to ensure matrix consistency and drop fractional parts
            freq_int = int(float(frequencia))
        except (ValueError, TypeError):
            raise TypeError(f"A frequência deve ser um valor numérico. Recebido: {type(frequencia)}")

        if not (0 <= freq_int <= 100):
            raise ValueError(f"Frequência inválida: {freq_int}. Deve estar entre 0 e 100.")

        return freq_int
