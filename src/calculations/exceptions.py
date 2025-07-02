"""
Módulo para exceções customizadas da camada de cálculo.
"""

class CalculationError(Exception):
    """Classe base para exceções relacionadas a cálculos."""
    pass

class InvalidInputError(CalculationError):
    """Lançada quando os dados de entrada para um cálculo são inválidos."""
    pass
