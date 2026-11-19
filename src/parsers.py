from src.grammar import Grammar


class ParseNode:
    def __init__(self, symbol, production=None, children=None, is_terminal=False):
        self.symbol = symbol
        self.production = production  # tuple (lhs, rhs) when nonterminal
        self.children = children if children is not None else []
        self.is_terminal = is_terminal
        self.attributes = {"lexval": symbol} if is_terminal else {}


class LL1Parser:
    def __init__(self, grammar: Grammar, first_map, follow_map):
        self.grammar = grammar
        self.first = first_map
        self.follow = follow_map
        self.table = {}  # (nonterminal, terminal_or_$) -> rhs
        self.is_ll1 = self._build_table()

    def _build_table(self):
        table = {}
        is_valid = True

        for nt in self.grammar.nonterminals:
            for alt in self.grammar.productions[nt]:
                first_alpha = self.grammar.first_of_string(alt, self.first)

                for term in first_alpha:
                    if term == "e":
                        continue
                    key = (nt, term)
                    if key in table and table[key] != alt:
                        is_valid = False
                    table[key] = alt

                if "e" in first_alpha:
                    for b in self.follow[nt]:
                        key = (nt, b)
                        if key in table and table[key] != alt:
                            is_valid = False
                        table[key] = alt

        self.table = table
        return is_valid

    def parse(self, input_str, build_tree=False):
        if not self.is_ll1:
            return False, None

        if input_str == "e":
            tokens = ["$"]
        else:
            if "e" in input_str or "$" in input_str:
                return False, None
            for ch in input_str:
                if ch not in self.grammar.terminals:
                    return False, None
            tokens = list(input_str) + ["$"]

        stack = ["$", self.grammar.start]
        root = ParseNode(self.grammar.start, is_terminal=False) if build_tree else None
        node_stack = [None, root] if build_tree else None

        idx = 0
        while stack:
            top = stack.pop()
            cur_node = node_stack.pop() if build_tree else None
            cur_tok = tokens[idx]

            if top == cur_tok:
                if top == "$":
                    return True, root
                idx += 1
            elif top in self.grammar.nonterminals:
                prod_rhs = self.table.get((top, cur_tok))
                if prod_rhs is None:
                    return False, None

                if build_tree and cur_node is not None:
                    cur_node.production = (top, prod_rhs)

                if prod_rhs != "e":
                    child_nodes = []
                    for sym in reversed(prod_rhs):
                        stack.append(sym)
                        if build_tree:
                            is_t = sym not in self.grammar.nonterminals
                            child = ParseNode(sym, is_terminal=is_t)
                            child_nodes.append(child)
                            node_stack.append(child)
                    if build_tree and cur_node is not None:
                        cur_node.children = list(reversed(child_nodes))
                else:
                    if build_tree and cur_node is not None:
                        cur_node.children = [ParseNode("e", is_terminal=True)]
            else:
                return False, None

        return False, None


class SLR1Parser:
    def __init__(self, grammar: Grammar, first_map, follow_map):
        self.grammar = grammar
        self.first = first_map
        self.follow = follow_map
        self.aug_start = self._choose_aug_start()
        self.prods = []
        self.states = []
        self.transitions = {}  # (state_id, symbol) -> next_state_id
        self.action = {}  # (state_id, term_or_$) -> ("shift", s) | ("reduce", prod_id) | ("accept", None)
        self.goto = {}  # (state_id, nt) -> next_state_id
        self.is_slr1 = self._build_automaton_and_tables()

    def _choose_aug_start(self):
        for ch in "ZXYWVUTRQPONMLKJIHGFEDCBA":
            if ch not in self.grammar.nonterminals:
                return ch
        return "S'"

    def _build_automaton_and_tables(self):
        self.prods.append((0, self.aug_start, [self.grammar.start]))
        pid = 1
        for nt in self.grammar.nonterminals:
            for alt in self.grammar.productions[nt]:
                rhs = ["e"] if alt == "e" else list(alt)
                self.prods.append((pid, nt, rhs))
                pid += 1

        start_item = (0, 0)
        c0 = self.closure({start_item})
        self.states = [c0]
        state_to_id = {frozenset(c0): 0}

        symbols = list(self.grammar.nonterminals) + list(self.grammar.terminals)
        queue = [0]
        head = 0
        while head < len(queue):
            sid = queue[head]
            head += 1
            cur_set = self.states[sid]
            for sym in symbols:
                nxt = self.goto_set(cur_set, sym)
                if not nxt:
                    continue
                frozen = frozenset(nxt)
                if frozen not in state_to_id:
                    nid = len(self.states)
                    state_to_id[frozen] = nid
                    self.states.append(nxt)
                    queue.append(nid)
                self.transitions[(sid, sym)] = state_to_id[frozen]

        conflict_free = True
        for sid, item_set in enumerate(self.states):
            for prod_id, dot in item_set:
                _, lhs, rhs = self.prods[prod_id]
                is_epsilon = rhs == ["e"]
                if not is_epsilon and dot < len(rhs):
                    sym = rhs[dot]
                    if sym in self.grammar.terminals:
                        target = self.transitions[(sid, sym)]
                        op = ("shift", target)
                        key = (sid, sym)
                        if key in self.action and self.action[key] != op:
                            conflict_free = False
                        self.action[key] = op
                else:
                    if prod_id == 0:
                        key = (sid, "$")
                        op = ("accept", None)
                        if key in self.action and self.action[key] != op:
                            conflict_free = False
                        self.action[key] = op
                    else:
                        for sym in self.follow[lhs]:
                            key = (sid, sym)
                            op = ("reduce", prod_id)
                            if key in self.action and self.action[key] != op:
                                conflict_free = False
                            self.action[key] = op

            for nt in self.grammar.nonterminals:
                if (sid, nt) in self.transitions:
                    self.goto[(sid, nt)] = self.transitions[(sid, nt)]

        return conflict_free

    def closure(self, items):
        closure_set = set(items)
        changed = True
        while changed:
            changed = False
            new_items = set()
            for prod_id, dot in closure_set:
                _, _, rhs = self.prods[prod_id]
                if rhs != ["e"] and dot < len(rhs):
                    sym = rhs[dot]
                    if sym in self.grammar.nonterminals:
                        for p_id, p_lhs, _ in self.prods:
                            if p_lhs == sym:
                                item = (p_id, 0)
                                if item not in closure_set:
                                    new_items.add(item)
            if new_items:
                closure_set.update(new_items)
                changed = True
        return closure_set

    def goto_set(self, items, symbol):
        moved = set()
        for prod_id, dot in items:
            _, _, rhs = self.prods[prod_id]
            if rhs != ["e"] and dot < len(rhs) and rhs[dot] == symbol:
                moved.add((prod_id, dot + 1))
        if not moved:
            return set()
        return self.closure(moved)

    def parse(self, input_str, build_tree=False):
        if not self.is_slr1:
            return False, None

        if input_str == "e":
            tokens = ["$"]
        else:
            if "e" in input_str or "$" in input_str:
                return False, None
            for ch in input_str:
                if ch not in self.grammar.terminals:
                    return False, None
            tokens = list(input_str) + ["$"]

        state_stack = [0]
        node_stack = [] if build_tree else None

        idx = 0
        while True:
            state = state_stack[-1]
            tok = tokens[idx]
            act = self.action.get((state, tok))
            if act is None:
                return False, None

            kind, val = act
            if kind == "shift":
                state_stack.append(val)
                if build_tree:
                    node_stack.append(ParseNode(tok, is_terminal=True))
                idx += 1
            elif kind == "reduce":
                _, lhs, rhs = self.prods[val]
                pop_count = 0 if rhs == ["e"] else len(rhs)
                popped_nodes = []
                for _ in range(pop_count):
                    state_stack.pop()
                    if build_tree:
                        popped_nodes.append(node_stack.pop())
                popped_nodes.reverse()

                if build_tree:
                    children = (
                        popped_nodes
                        if rhs != ["e"]
                        else [ParseNode("e", is_terminal=True)]
                    )
                    parent = ParseNode(
                        lhs,
                        production=(lhs, "".join(rhs)),
                        children=children,
                        is_terminal=False,
                    )
                    node_stack.append(parent)

                top_state = state_stack[-1]
                next_state = self.goto.get((top_state, lhs))
                if next_state is None:
                    return False, None
                state_stack.append(next_state)
            elif kind == "accept":
                root = node_stack[-1] if (build_tree and node_stack) else None
                return True, root