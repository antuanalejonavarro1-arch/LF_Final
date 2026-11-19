"""Gramática libre de contexto: lectura de la entrada y consultas básicas.

Convenciones del enunciado (sección 2.2):
  - 'S' es el símbolo inicial y los no terminales son letras mayúsculas.
  - 'e' representa la cadena vacía (ε) y '$' es el marcador de fin de cadena.
"""
import sys

EPSILON = "e"   # la cadena vacía se escribe 'e'
END = "$"       # marcador de fin de cadena (el programa lo agrega a cada entrada)
START = "S"     # símbolo inicial


def _read_nonblank_line(stream, error_message):
    """Lee la siguiente línea que no esté en blanco; falla si se acaba la entrada."""
    while True:
        raw = stream.readline()
        if raw == "":
            raise ValueError(error_message)
        line = raw.strip().lstrip("\ufeff").strip()  # lstrip: tolera un BOM al inicio del archivo
        if line != "":
            return line


class Grammar:
    def __init__(self, nonterminals, productions):
        self.start = START
        self.nonterminals = nonterminals    # lista, en el orden en que aparecen en la entrada
        self.productions = productions      # dict: no terminal -> lista de alternativas (str)
        self._nonterminal_set = set(nonterminals)
        self.terminals = self._find_terminals()  # lista ordenada (ASCII)

    # ------------------------------------------------------------------ lectura
    @classmethod
    def from_stream(cls, stream=sys.stdin):
        """Lee: una línea con n, y luego n líneas con el formato  A -> alt1 alt2 ..."""
        n = int(_read_nonblank_line(stream, "Empty grammar input"))
        nonterminals = []
        productions = {}
        for _ in range(n):
            line = _read_nonblank_line(stream, "Incomplete grammar input")
            lhs, rhs = line.split("->", 1)
            lhs = lhs.strip()
            nonterminals.append(lhs)
            productions[lhs] = rhs.split()  # las alternativas van separadas por espacios
        return cls(nonterminals, productions)

    def _find_terminals(self):
        """Terminal = cualquier símbolo de un lado derecho que no sea no terminal, 'e' ni '$'."""
        found = set()
        for _, alternative in self.all_productions():
            for symbol in alternative:
                if symbol not in self._nonterminal_set and symbol not in (EPSILON, END):
                    found.add(symbol)
        return sorted(found)

    # ---------------------------------------------------------------- consultas
    def is_nonterminal(self, symbol):
        return symbol in self._nonterminal_set

    def all_productions(self):
        """Recorre todas las producciones como pares (lado izquierdo, alternativa)."""
        for lhs in self.nonterminals:
            for alternative in self.productions[lhs]:
                yield lhs, alternative

    def tokenize(self, text):
        """Convierte la cadena de entrada en la lista de tokens + '$'.

        Devuelve None si la cadena tiene símbolos que no son terminales de la gramática
        (esto también rechaza 'e' y '$' dentro de la cadena). La cadena vacía llega como 'e'.
        """
        if text == EPSILON:
            return [END]
        if any(ch not in self.terminals for ch in text):
            return None
        return list(text) + [END]
