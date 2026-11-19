import sys


class Grammar:
    def __init__(self, start_symbol, nonterminals, terminals, productions):
        self.start = start_symbol
        self.nonterminals = nonterminals
        self.terminals = terminals
        self.productions = productions  # dict[str, list[str]]

    @classmethod
    def from_stream(cls, stream=sys.stdin):
        first_line = ""
        while True:
            raw = stream.readline()
            if raw == "":
                raise ValueError("Empty grammar input")
            first_line = raw.strip()
            if first_line != "":
                break

        n = int(first_line)
        nonterminals = []
        productions = {}
        raw_alts = []

        for _ in range(n):
            line = ""
            while line == "":
                raw = stream.readline()
                if raw == "":
                    raise ValueError("Incomplete grammar input")
                line = raw.strip()

            lhs, rhs = line.split("->", 1)
            lhs = lhs.strip()
            alts = rhs.strip().split()
            nonterminals.append(lhs)
            productions[lhs] = alts
            raw_alts.extend(alts)

        nt_set = set(nonterminals)
        terminals = set()
        for alt in raw_alts:
            if alt == "e":
                continue
            for ch in alt:
                if ch not in nt_set and ch not in {"e", "$"}:
                    terminals.add(ch)

        return cls("S", nonterminals, sorted(terminals), productions)

    def compute_first(self):
        first = {nt: set() for nt in self.nonterminals}
        for t in self.terminals:
            first[t] = {t}
        first["e"] = {"e"}
        first["$"] = {"$"}

        changed = True
        while changed:
            changed = False
            for nt in self.nonterminals:
                for alt in self.productions[nt]:
                    if alt == "e":
                        if "e" not in first[nt]:
                            first[nt].add("e")
                            changed = True
                        continue

                    nullable_prefix = True
                    for sym in alt:
                        sym_first = first.get(sym, {sym})
                        for tok in sym_first:
                            if tok != "e" and tok not in first[nt]:
                                first[nt].add(tok)
                                changed = True
                        if "e" not in sym_first:
                            nullable_prefix = False
                            break

                    if nullable_prefix and "e" not in first[nt]:
                        first[nt].add("e")
                        changed = True

        return first

    def first_of_string(self, seq, first_map):
        result = set()
        if seq == "" or seq == "e":
            result.add("e")
            return result

        nullable_all = True
        for sym in seq:
            sym_first = first_map.get(sym, {sym})
            result.update(tok for tok in sym_first if tok != "e")
            if "e" not in sym_first:
                nullable_all = False
                break

        if nullable_all:
            result.add("e")
        return result

    def compute_follow(self, first_map):
        follow = {nt: set() for nt in self.nonterminals}
        follow[self.start].add("$")

        changed = True
        while changed:
            changed = False
            for lhs in self.nonterminals:
                for alt in self.productions[lhs]:
                    if alt == "e":
                        continue
                    for idx, sym in enumerate(alt):
                        if sym not in follow:
                            continue
                        beta = alt[idx + 1 :]
                        first_beta = self.first_of_string(beta, first_map)
                        for tok in first_beta:
                            if tok != "e" and tok not in follow[sym]:
                                follow[sym].add(tok)
                                changed = True
                        if "e" in first_beta:
                            for tok in follow[lhs]:
                                if tok not in follow[sym]:
                                    follow[sym].add(tok)
                                    changed = True

        return follow

    def format_sets(self, first_map, follow_map):
        def sort_key(tok):
            if tok == "e":
                return (1, 0)
            if tok == "$":
                return (2, 0)
            return (0, ord(tok))

        out = []
        for nt in sorted(self.nonterminals):
            f_items = ",".join(sorted(first_map[nt], key=sort_key))
            fo_items = ",".join(sorted(follow_map[nt], key=sort_key))
            out.append(f"First({nt})={{{f_items}}}")
            out.append(f"Follow({nt})={{{fo_items}}}")
        return "\n".join(out)