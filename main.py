"""Punto de entrada. Lee la gramática de stdin y luego las cadenas, una por línea.

Uso:  python3 main.py [--sets] [--table] [--trace] [--sdd [--circular]] < entrada.txt
  --sets      imprime FIRST y FOLLOW
  --table     imprime la tabla LL(1), el autómata LR(0) y la tabla SLR(1)
  --trace     imprime la pila paso a paso en cada parseo
  --sdd       Ítem 3: evalúa la SDD de src/sample_sdd.py sobre el árbol de cada cadena
  --circular  (con --sdd) usa la variante circular de la SDD para mostrar la detección
"""
import sys

from src.grammar import Grammar
from src.first_follow import compute_first, compute_follow, format_sets
from src.ll1_parser import LL1Parser
from src.slr1_parser import SLR1Parser
from src.dependency_graph import SDDError
from src.sample_sdd import build_sample_sdd

MENU = "Select a parser (T: for LL(1), B: for SLR(1), Q: quit):"


def read_strings(stream):
    """Entrega las cadenas de entrada una por una; se detiene en la línea vacía o al acabar la entrada."""
    while True:
        line = stream.readline()
        text = line.rstrip("\r\n")
        if text == "":          # línea vacía (o fin de archivo): termina esta tanda de cadenas
            return
        yield text


# ----------------------------------------------------------------- Ítems 1 y 2
def parse_strings(parser, stream):
    """Imprime yes/no para cada cadena."""
    for text in read_strings(stream):
        accepted, _ = parser.parse(text)
        print("yes" if accepted else "no", flush=True)


def ask_parser_loop(ll1, slr1, stream):
    """Caso 1 (ambos parsers sirven): menú T / B / Q."""
    while True:
        print(MENU, flush=True)
        choice = stream.readline()
        if choice == "":
            return
        choice = choice.strip()
        if choice == "Q":
            return
        if choice == "T":
            parse_strings(ll1, stream)
        elif choice == "B":
            parse_strings(slr1, stream)


def run_parsing_mode(ll1, slr1):
    """Casos 1 a 4 de la sección 2.2.2 del enunciado."""
    if ll1.is_ll1 and slr1.is_slr1:
        ask_parser_loop(ll1, slr1, sys.stdin)
    elif ll1.is_ll1:
        print("Grammar is LL(1).", flush=True)
        parse_strings(ll1, sys.stdin)
    elif slr1.is_slr1:
        print("Grammar is SLR(1).", flush=True)
        parse_strings(slr1, sys.stdin)
    else:
        print("Grammar is neither LL(1) nor SLR(1).", flush=True)


def print_tables(ll1, slr1):
    if ll1.is_ll1:
        print(ll1.format_table(), flush=True)
    print(slr1.format_automaton(), flush=True)
    note = "" if slr1.is_slr1 else "\n(table has conflicts: not SLR(1))"
    print(slr1.format_table() + note, flush=True)


# --------------------------------------------------------------------- Ítem 3
def run_sdd_mode(grammar, ll1, slr1, circular):
    parser = slr1 if slr1.is_slr1 else (ll1 if ll1.is_ll1 else None)
    if parser is None:
        print("Grammar is neither LL(1) nor SLR(1).", flush=True)
        return
    evaluator = build_sample_sdd(circular=circular)
    try:
        evaluator.check_against_grammar(grammar)
        for text in read_strings(sys.stdin):
            if not evaluate_one_string(parser, evaluator, text):
                return                       # SDD circular o inválida: se detiene
    except SDDError as error:
        print(f"Invalid SDD: {error}", flush=True)


def evaluate_one_string(parser, evaluator, text):
    """Parsea, evalúa e imprime. Devuelve False si hay que detener el programa."""
    accepted, root = parser.parse(text, build_tree=True)
    if not accepted:
        print("no", flush=True)
        return True
    result = evaluator.evaluate_tree(root)
    if result["circular"]:
        print("SDD is circular", flush=True)
        return False
    print(evaluator.format_annotated_tree(root), flush=True)
    print("Evaluation order:", " -> ".join(result["order"]), flush=True)
    print(f"Result ({evaluator.main_attr}): {result['root_value']}", flush=True)
    return True


# ------------------------------------------------------------------------ main
def main():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8-sig")   # acepta archivos guardados con BOM
    flags = sys.argv[1:]

    grammar = Grammar.from_stream(sys.stdin)
    first = compute_first(grammar)
    follow = compute_follow(grammar, first)
    if "--sets" in flags:
        print(format_sets(grammar, first, follow), flush=True)

    ll1 = LL1Parser(grammar, first, follow)
    slr1 = SLR1Parser(grammar, follow)
    ll1.trace = slr1.trace = "--trace" in flags
    if "--table" in flags:
        print_tables(ll1, slr1)

    if "--sdd" in flags:
        run_sdd_mode(grammar, ll1, slr1, circular="--circular" in flags)
    else:
        run_parsing_mode(ll1, slr1)


if __name__ == "__main__":
    main()
