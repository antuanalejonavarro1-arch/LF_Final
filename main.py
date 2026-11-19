import sys
from src.grammar import Grammar
from src.parsers import LL1Parser, SLR1Parser
from src.sdd import build_sample_sdd


def run_string_loop(parser, stream):
    while True:
        line = stream.readline()
        if line == "":
            break
        s = line.rstrip("\r\n")
        if s == "":
            break
        ok, _ = parser.parse(s, build_tree=False)
        print("yes" if ok else "no", flush=True)


def run_sdd_loop(parser, evaluator, stream):
    while True:
        line = stream.readline()
        if line == "":
            break
        s = line.rstrip("\r\n")
        if s == "":
            break
        ok, root = parser.parse(s, build_tree=True)
        if not ok or root is None:
            print("no", flush=True)
            continue
        res = evaluator.evaluate_tree(root)
        if res.get("circular"):
            print("SDD is circular", flush=True)
            return
        print(evaluator.format_annotated_tree(root), flush=True)
        print("Evaluation order:", " -> ".join(res["order"]), flush=True)
        print(f"Result ({evaluator.main_attr}): {res['root_value']}", flush=True)


def main():
    args = sys.argv[1:]
    show_sets = "--sets" in args
    run_sdd = "--sdd" in args
    circular = "--circular" in args

    grammar = Grammar.from_stream(sys.stdin)
    first_map = grammar.compute_first()
    follow_map = grammar.compute_follow(first_map)

    if show_sets:
        print(grammar.format_sets(first_map, follow_map), flush=True)

    ll1 = LL1Parser(grammar, first_map, follow_map)
    slr1 = SLR1Parser(grammar, first_map, follow_map)

    if run_sdd:
        evaluator = build_sample_sdd(circular=circular)
        parser = slr1 if slr1.is_slr1 else (ll1 if ll1.is_ll1 else None)
        if parser is None:
            print("Grammar is neither LL(1) nor SLR(1).", flush=True)
            return
        run_sdd_loop(parser, evaluator, sys.stdin)
        return

    if ll1.is_ll1 and slr1.is_slr1:
        while True:
            print(
                "Select a parser (T: for LL(1), B: for SLR (1), Q: quit):",
                flush=True,
            )
            choice_line = sys.stdin.readline()
            if choice_line == "":
                break
            choice = choice_line.strip()
            if choice == "":
                continue
            if choice == "Q":
                break
            if choice == "T":
                run_string_loop(ll1, sys.stdin)
            elif choice == "B":
                run_string_loop(slr1, sys.stdin)
    elif ll1.is_ll1:
        print("Grammar is LL(1).", flush=True)
        run_string_loop(ll1, sys.stdin)
    elif slr1.is_slr1:
        print("Grammar is SLR(1).", flush=True)
        run_string_loop(slr1, sys.stdin)
    else:
        print("Grammar is neither LL(1) nor SLR(1).", flush=True)


if __name__ == "__main__":
    main()