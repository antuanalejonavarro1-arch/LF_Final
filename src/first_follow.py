"""Conjuntos FIRST y FOLLOW (Aho et al., 2ª ed., sección 4.4.2).

Ambos se calculan por iteración hasta punto fijo: se aplican las reglas del libro
una y otra vez hasta que ningún conjunto crece.
"""
from src.grammar import EPSILON, END


def _add(target, items):
    """Agrega 'items' al conjunto 'target'. Devuelve True si el conjunto creció."""
    size_before = len(target)
    target |= items
    return len(target) != size_before


def first_of_string(symbols, first):
    """FIRST(X1 X2 ... Xn): se agrega FIRST(Xi) mientras X1..X(i-1) puedan derivar ε.

    Si todos los Xi pueden derivar ε, el resultado también contiene ε.
    Los terminales no están en el mapa: su FIRST es el propio terminal.
    """
    result = set()
    for symbol in symbols:
        symbol_first = first.get(symbol, {symbol})
        result |= symbol_first - {EPSILON}
        if EPSILON not in symbol_first:
            return result            # Xi no se anula: los símbolos siguientes no aportan
    result.add(EPSILON)              # toda la cadena (o la cadena vacía) deriva ε
    return result


def compute_first(grammar):
    """FIRST de todos los símbolos: no terminales, terminales, 'e' y '$'."""
    first = {nt: set() for nt in grammar.nonterminals}
    for terminal in grammar.terminals:
        first[terminal] = {terminal}              # regla 1: FIRST(a) = {a}
    first[EPSILON] = {EPSILON}
    first[END] = {END}

    changed = True
    while changed:
        changed = False
        for lhs, alternative in grammar.all_productions():
            # reglas 2 y 3: FIRST(A) incluye FIRST(alternativa) para cada A -> alternativa
            changed |= _add(first[lhs], first_of_string(alternative, first))
    return first


def compute_follow(grammar, first):
    """FOLLOW de cada no terminal."""
    follow = {nt: set() for nt in grammar.nonterminals}
    follow[grammar.start].add(END)                # regla 1: $ está en FOLLOW(S)

    changed = True
    while changed:
        changed = False
        for lhs, alternative in grammar.all_productions():
            if alternative == EPSILON:
                continue
            for i, symbol in enumerate(alternative):
                if not grammar.is_nonterminal(symbol):
                    continue
                # Para  A -> alfa B beta:  beta es lo que sigue a B en esta producción
                first_beta = first_of_string(alternative[i + 1:], first)
                changed |= _add(follow[symbol], first_beta - {EPSILON})   # regla 2
                if EPSILON in first_beta:                                  # regla 3
                    changed |= _add(follow[symbol], follow[lhs])
    return follow


def format_sets(grammar, first, follow):
    """Texto de --sets: un par de líneas por no terminal, en orden alfabético.

    Dentro de las llaves: terminales en orden ASCII, luego 'e' y por último '$'.
    """
    def order(token):
        if token == EPSILON:
            return (1, 0)
        if token == END:
            return (2, 0)
        return (0, ord(token))

    lines = []
    for nt in sorted(grammar.nonterminals):
        first_text = ", ".join(sorted(first[nt], key=order))
        follow_text = ", ".join(sorted(follow[nt], key=order))
        lines.append(f"First({nt}) = {{{first_text}}}")
        lines.append(f"Follow({nt}) = {{{follow_text}}}")
    return "\n".join(lines)
