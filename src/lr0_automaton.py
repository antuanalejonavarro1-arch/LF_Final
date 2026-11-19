"""Colección canónica de conjuntos de ítems LR(0) (Aho et al., sección 4.6.2).

Un ítem es un par (índice de producción, posición del punto):  (3, 1)  significa
"producción 3 con el punto después del primer símbolo del lado derecho".
"""
from collections import namedtuple
from src.grammar import EPSILON

# rhs es una lista de símbolos; para A -> ε la lista está vacía (así el ítem (A -> .) ya está completo).
Production = namedtuple("Production", "index lhs rhs")


def rhs_text(rhs):
    return "".join(rhs) or EPSILON


class LR0Automaton:
    def __init__(self, grammar):
        self.grammar = grammar
        self.productions = self._augmented_productions()
        self.states = []         # cada estado es un frozenset de ítems; el índice es el número del estado
        self.transitions = {}    # (estado, símbolo) -> estado destino
        self._build()

    # ------------------------------------------------ gramática aumentada
    def _augmented_productions(self):
        """Producción 0 = Z -> S (gramática aumentada); luego las originales, en orden."""
        aug_start = next((c for c in "ZYXWVUTRQPONMLKJIHGFEDCBA"
                          if c not in self.grammar.nonterminals), "S'")
        productions = [Production(0, aug_start, [self.grammar.start])]
        for lhs, alternative in self.grammar.all_productions():
            rhs = [] if alternative == EPSILON else list(alternative)
            productions.append(Production(len(productions), lhs, rhs))
        return productions

    def _productions_of(self, nonterminal):
        return [p for p in self.productions if p.lhs == nonterminal]

    # ------------------------------------------------ CLOSURE y GOTO
    def closure(self, items):
        """CLOSURE(I): si hay un ítem A -> alfa . B beta, se agregan los ítems B -> . gamma."""
        result = set(items)
        pending = list(items)
        while pending:
            index, dot = pending.pop()
            rhs = self.productions[index].rhs
            if dot < len(rhs) and self.grammar.is_nonterminal(rhs[dot]):
                for production in self._productions_of(rhs[dot]):
                    new_item = (production.index, 0)
                    if new_item not in result:
                        result.add(new_item)
                        pending.append(new_item)
        return frozenset(result)

    def goto(self, items, symbol):
        """GOTO(I, X): mueve el punto sobre X en los ítems que lo permiten y cierra el resultado."""
        moved = {(index, dot + 1) for index, dot in items
                 if dot < len(self.productions[index].rhs)
                 and self.productions[index].rhs[dot] == symbol}
        return self.closure(moved) if moved else frozenset()

    # ------------------------------------------------ construcción del autómata
    def _build(self):
        symbols = list(self.grammar.nonterminals) + list(self.grammar.terminals)
        self.states = [self.closure({(0, 0)})]            # estado 0 = CLOSURE({Z -> .S})
        state_ids = {self.states[0]: 0}
        current = 0
        while current < len(self.states):                 # los estados nuevos se agregan al final
            for symbol in symbols:
                target = self.goto(self.states[current], symbol)
                if not target:
                    continue
                if target not in state_ids:
                    state_ids[target] = len(self.states)
                    self.states.append(target)
                self.transitions[(current, symbol)] = state_ids[target]
            current += 1

    # ------------------------------------------------ impresión
    def item_text(self, item):
        index, dot = item
        production = self.productions[index]
        before = "".join(production.rhs[:dot])
        after = "".join(production.rhs[dot:])
        return f"{production.lhs} -> {before}.{after}"

    def format(self):
        lines = ["LR(0) automaton:"]
        for state_id, items in enumerate(self.states):
            lines.append(f"I{state_id}:")
            lines += ["    " + self.item_text(item) for item in sorted(items)]
            lines += [f"    --{symbol}--> I{target}"
                      for (source, symbol), target in sorted(self.transitions.items())
                      if source == state_id]
        return "\n".join(lines)
