"""Parser SLR(1): tablas ACTION/GOTO (sección 4.6.4) y algoritmo de parseo LR (sección 4.6.3)."""
from src.grammar import END
from src.lr0_automaton import LR0Automaton, rhs_text
from src.parse_tree import ParseNode, epsilon_leaf


class SLR1Parser:
    def __init__(self, grammar, follow):
        self.grammar = grammar
        self.follow = follow
        self.automaton = LR0Automaton(grammar)
        self.trace = False                # si es True, parse() imprime la pila paso a paso
        self.action = {}                  # (estado, terminal o $) -> ("shift", s) | ("reduce", p) | ("accept",)
        self.goto = {}                    # (estado, no terminal) -> estado
        self.is_slr1 = self._build_tables()

    # ------------------------------------------------------------------ tablas
    def _set_action(self, state, terminal, action):
        """Escribe una entrada de ACTION. Devuelve False si choca con otra distinta (conflicto)."""
        already_there = self.action.setdefault((state, terminal), action)
        return already_there == action

    def _build_tables(self):
        """Llena ACTION y GOTO. La gramática es SLR(1) si no hay conflictos shift/reduce ni reduce/reduce."""
        productions = self.automaton.productions
        conflict_free = True

        for state, items in enumerate(self.automaton.states):
            for index, dot in items:
                production = productions[index]
                if dot < len(production.rhs):
                    # Ítem  A -> alfa . a beta  con 'a' terminal  =>  desplazar
                    symbol = production.rhs[dot]
                    if not self.grammar.is_nonterminal(symbol):
                        target = self.automaton.transitions[(state, symbol)]
                        conflict_free &= self._set_action(state, symbol, ("shift", target))
                elif index == 0:
                    # Ítem  Z -> S .  =>  aceptar con $
                    conflict_free &= self._set_action(state, END, ("accept",))
                else:
                    # Ítem completo  A -> alfa .  =>  reducir para cada terminal de FOLLOW(A)
                    for terminal in self.follow[production.lhs]:
                        conflict_free &= self._set_action(state, terminal, ("reduce", index))

        # GOTO: las transiciones del autómata con no terminales
        for (state, symbol), target in self.automaton.transitions.items():
            if self.grammar.is_nonterminal(symbol):
                self.goto[(state, symbol)] = target
        return conflict_free

    def format_automaton(self):
        return self.automaton.format()

    def format_table(self):
        terminals = sorted(self.grammar.terminals) + [END]
        nonterminals = sorted(self.grammar.nonterminals)
        header = f"{'st':<5}" + "".join(f"{t:<8}" for t in terminals) + "| " \
                 + "".join(f"{n:<5}" for n in nonterminals)
        lines = ["SLR(1) table:", header]
        for state in range(len(self.automaton.states)):
            actions = [self._action_text(self.action.get((state, t))) for t in terminals]
            gotos = [str(self.goto.get((state, n), "")) for n in nonterminals]
            lines.append(f"{state:<5}" + "".join(f"{a:<8}" for a in actions) + "| "
                         + "".join(f"{g:<5}" for g in gotos))
        lines.append("Productions: " + "; ".join(
            f"{p.index}: {p.lhs}->{rhs_text(p.rhs)}" for p in self.automaton.productions))
        return "\n".join(lines)

    @staticmethod
    def _action_text(action):
        if action is None:
            return ""
        if action[0] == "shift":
            return f"s{action[1]}"
        if action[0] == "reduce":
            return f"r{action[1]}"
        return "acc"

    # ------------------------------------------------------------------ parseo
    def parse(self, text, build_tree=False):
        """Devuelve (aceptada?, raíz del árbol o None)."""
        if not self.is_slr1:
            return False, None
        tokens = self.grammar.tokenize(text)
        if tokens is None:
            return False, None

        states = [0]          # pila de estados
        symbols = []          # pila de pares (símbolo, nodo del árbol), paralela a states[1:]
        pos = 0
        if self.trace:
            print(f"{'STATES':<24}{'SYMBOLS':<14}{'INPUT':<14}ACTION")

        while True:
            lookahead = tokens[pos]
            action = self.action.get((states[-1], lookahead))
            if self.trace:
                self._print_trace_row(states, symbols, tokens[pos:], action)
            if action is None:
                return False, None                        # celda vacía: error sintáctico

            if action[0] == "shift":
                leaf = ParseNode(lookahead, is_terminal=True) if build_tree else None
                symbols.append((lookahead, leaf))
                states.append(action[1])
                pos += 1
            elif action[0] == "reduce":
                if not self._reduce(self.automaton.productions[action[1]], states, symbols, build_tree):
                    return False, None
            else:                                         # accept
                root = symbols[-1][1] if symbols else None
                return True, root

    def _reduce(self, production, states, symbols, build_tree):
        """Reduce por A -> alfa: saca |alfa| elementos de las pilas y mete A usando GOTO."""
        count = len(production.rhs)
        popped = symbols[len(symbols) - count:]
        del symbols[len(symbols) - count:]
        del states[len(states) - count:]

        node = None
        if build_tree:
            node = ParseNode(production.lhs)
            node.production = (production.lhs, rhs_text(production.rhs))
            node.children = [child for _, child in popped] or [epsilon_leaf()]

        next_state = self.goto.get((states[-1], production.lhs))
        if next_state is None:
            return False
        symbols.append((production.lhs, node))
        states.append(next_state)
        return True

    def _print_trace_row(self, states, symbols, remaining_input, action):
        if action is None:
            description = "error"
        elif action[0] == "shift":
            description = f"shift {action[1]}"
        elif action[0] == "reduce":
            production = self.automaton.productions[action[1]]
            description = f"reduce {production.lhs} -> {rhs_text(production.rhs)}"
        else:
            description = "accept"
        print(f"{' '.join(map(str, states)):<24}{''.join(s for s, _ in symbols):<14}"
              f"{''.join(remaining_input):<14}{description}")
