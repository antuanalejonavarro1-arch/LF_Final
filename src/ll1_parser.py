"""Parser LL(1) predictivo, no recursivo y dirigido por tabla (Aho et al., secciones 4.4.3 y 4.4.4)."""
from src.grammar import EPSILON, END
from src.first_follow import first_of_string
from src.parse_tree import ParseNode, epsilon_leaf


class LL1Parser:
    def __init__(self, grammar, first, follow):
        self.grammar = grammar
        self.first = first
        self.follow = follow
        self.trace = False                  # si es True, parse() imprime la pila paso a paso
        self.table = {}                     # (no terminal, terminal o $) -> alternativa
        self.is_ll1 = self._build_table()

    # ------------------------------------------------------------------- tabla
    def _predict_set(self, lhs, alternative):
        """Terminales con los que se elige  lhs -> alternativa  (algoritmo 4.31 del libro):
        FIRST(alternativa) sin ε, más FOLLOW(lhs) si la alternativa puede derivar ε."""
        first_alt = first_of_string(alternative, self.first)
        predict = first_alt - {EPSILON}
        if EPSILON in first_alt:
            predict |= self.follow[lhs]
        return predict

    def _build_table(self):
        """Llena la tabla M[A, a]. La gramática es LL(1) si ninguna celda recibe dos producciones."""
        is_ll1 = True
        for lhs, alternative in self.grammar.all_productions():
            for terminal in self._predict_set(lhs, alternative):
                already_there = self.table.setdefault((lhs, terminal), alternative)
                if already_there != alternative:
                    is_ll1 = False          # conflicto: dos alternativas para la misma celda
        return is_ll1

    def format_table(self):
        columns = sorted(self.grammar.terminals) + [END]
        lines = ["LL(1) table:", "      " + "".join(f"{c:<10}" for c in columns)]
        for nt in sorted(self.grammar.nonterminals):
            cells = []
            for terminal in columns:
                alternative = self.table.get((nt, terminal))
                cells.append(f"{nt}->{alternative}" if alternative is not None else "-")
            lines.append(f"{nt:<6}" + "".join(f"{cell:<10}" for cell in cells))
        return "\n".join(lines)

    # ------------------------------------------------------------------ parseo
    def parse(self, text, build_tree=False):
        """Devuelve (aceptada?, raíz del árbol o None)."""
        if not self.is_ll1:
            return False, None
        tokens = self.grammar.tokenize(text)
        if tokens is None:
            return False, None

        root = ParseNode(self.grammar.start) if build_tree else None
        # La pila guarda pares (símbolo, nodo del árbol); el tope es el último elemento.
        stack = [(END, None), (self.grammar.start, root)]
        pos = 0                                       # posición del símbolo de entrada actual
        if self.trace:
            print(f"{'STACK':<16}{'INPUT':<16}ACTION")

        while stack:
            symbol, node = stack.pop()
            lookahead = tokens[pos]
            if self.trace:
                self._print_trace_row(symbol, stack, tokens[pos:])

            if symbol == lookahead:                   # terminal (o $) en el tope: coincide
                if symbol == END:
                    return True, root
                pos += 1
            elif self.grammar.is_nonterminal(symbol):  # no terminal: consultar la tabla
                alternative = self.table.get((symbol, lookahead))
                if alternative is None:
                    return False, None                # celda vacía: error sintáctico
                self._expand(symbol, alternative, node, stack, build_tree)
            else:
                return False, None                    # terminal distinto del de la entrada
        return False, None

    def _expand(self, lhs, alternative, node, stack, build_tree):
        """Reemplaza el no terminal del tope por el lado derecho de la producción elegida."""
        symbols = [] if alternative == EPSILON else list(alternative)
        children = [ParseNode(s, is_terminal=not self.grammar.is_nonterminal(s)) for s in symbols]
        if build_tree:
            node.production = (lhs, alternative)
            node.children = children if symbols else [epsilon_leaf()]
        nodes = children if build_tree else [None] * len(symbols)
        # Se apila de derecha a izquierda para que el primer símbolo quede en el tope.
        for symbol, child in reversed(list(zip(symbols, nodes))):
            stack.append((symbol, child))

    def _print_trace_row(self, symbol, stack, remaining_input):
        # El libro muestra la pila con el tope a la izquierda.
        shown_stack = symbol + "".join(s for s, _ in reversed(stack))
        if symbol == remaining_input[0]:
            action = "match " + symbol
        elif (symbol, remaining_input[0]) in self.table:
            action = f"output {symbol} -> {self.table[(symbol, remaining_input[0])]}"
        else:
            action = "error"
        print(f"{shown_stack:<16}{''.join(remaining_input):<16}{action}")
