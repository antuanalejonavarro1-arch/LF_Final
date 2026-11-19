"""Nodo del árbol de derivación, compartido por los dos parsers y por el evaluador de la SDD."""
from src.grammar import EPSILON


class ParseNode:
    def __init__(self, symbol, is_terminal=False):
        self.symbol = symbol
        self.is_terminal = is_terminal
        self.production = None   # (lhs, alternativa) usada en este nodo; solo para no terminales
        self.children = []
        # Los terminales traen su valor léxico: lexval es el propio carácter.
        self.attributes = {"lexval": symbol} if is_terminal else {}


def epsilon_leaf():
    """Hoja 'e' que cuelga de un nodo cuya producción fue A -> ε."""
    return ParseNode(EPSILON, is_terminal=True)
