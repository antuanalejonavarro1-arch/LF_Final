from collections import deque


class SDDRule:
    def __init__(self, lhs, rhs, defined_attr, used_attrs, compute_fn):
        self.lhs = lhs
        self.rhs = rhs
        self.defined_attr = defined_attr
        self.used_attrs = list(used_attrs)
        self.compute_fn = compute_fn


class SDDEvaluator:
    def __init__(self, sdd_spec, main_attr):
        self.sdd_spec = sdd_spec
        self.main_attr = main_attr

    def _assign_node_ids(self, root):
        counter = [0]
        nodes_by_id = {}

        def dfs(node):
            nid = f"n{counter[0]}"
            counter[0] += 1
            node.node_id = nid
            nodes_by_id[nid] = node
            for ch in node.children:
                dfs(ch)

        dfs(root)
        return nodes_by_id

    def _build_dependency_graph(self, root):
        nodes_by_id = self._assign_node_ids(root)
        attr_values = {}
        attr_owners = {}

        def register_attrs(node):
            for k, v in node.attributes.items():
                attr_values[(node.node_id, k)] = v
                attr_owners[(node.node_id, k)] = node
            for ch in node.children:
                register_attrs(ch)

        register_attrs(root)

        adj = {}
        in_degree = {}
        rule_lookup = {}

        def add_vertex(key):
            if key not in adj:
                adj[key] = set()
            if key not in in_degree:
                in_degree[key] = 0

        for key in attr_values:
            add_vertex(key)

        def instantiate(node):
            if node.is_terminal:
                return
            prod_key = node.production
            builders = self.sdd_spec.get(prod_key, [])
            child_ids = [ch.node_id for ch in node.children]
            ctx = {
                "parent": node.node_id,
                "parent_node": node,
                "children": child_ids,
                "child_nodes": node.children,
            }
            for build_rule in builders:
                r = build_rule(ctx)
                target = r["defines"]
                deps = r["uses"]
                fn = r["fn"]

                add_vertex(target)
                attr_owners[target] = node
                rule_lookup[target] = (node, deps, fn)

                for src in deps:
                    add_vertex(src)
                    if target not in adj[src]:
                        adj[src].add(target)
                        in_degree[target] += 1

            for ch in node.children:
                instantiate(ch)

        instantiate(root)
        return nodes_by_id, attr_values, attr_owners, adj, in_degree, rule_lookup

    def _topological_sort(self, adj, in_degree):
        deg = dict(in_degree)
        queue = deque([k for k, d in deg.items() if d == 0])
        order = []

        while queue:
            u = queue.popleft()
            order.append(u)
            for v in sorted(adj.get(u, ())):
                deg[v] -= 1
                if deg[v] == 0:
                    queue.append(v)

        if len(order) != len(deg):
            return None
        return order

    def evaluate_tree(self, root):
        nodes_by_id, attr_values, attr_owners, adj, in_degree, rule_lookup = (
            self._build_dependency_graph(root)
        )
        order = self._topological_sort(adj, in_degree)
        if order is None:
            return {"circular": True}

        eval_order_labels = []
        for key in order:
            nid, aname = key
            node = nodes_by_id[nid]
            eval_order_labels.append(f"{node.symbol}({nid}).{aname}")
            if key in rule_lookup:
                owner_node, deps, fn = rule_lookup[key]
                dep_vals = [attr_values.get(d) for d in deps]
                val = fn(owner_node, *dep_vals)
                attr_values[key] = val
                owner_node.attributes[aname] = val

        return {
            "circular": False,
            "order": eval_order_labels,
            "root_value": attr_values.get((root.node_id, self.main_attr)),
        }

    def format_annotated_tree(self, root):
        lines = []

        def walk(node, depth):
            indent = "  " * depth
            attrs_str = ", ".join(f"{k}={v}" for k, v in sorted(node.attributes.items()))
            prod_str = ""
            if not node.is_terminal and node.production:
                prod_str = f" [{node.production[0]}->{node.production[1]}]"
            lines.append(f"{indent}{node.symbol}{prod_str} {{{attrs_str}}}")
            for ch in node.children:
                walk(ch, depth + 1)

        walk(root, 0)
        return "\n".join(lines)


def build_sample_sdd(circular=False):
    spec = {
        ("S", "B"): [
            lambda ctx: {
                "defines": (ctx["children"][0], "lvl"),
                "uses": [],
                "fn": lambda _n: 1,
            },
            lambda ctx: {
                "defines": (ctx["parent"], "cost"),
                "uses": [(ctx["children"][0], "cost")],
                "fn": lambda _n, b_cost: b_cost,
            },
        ],
        ("B", "[T]B"): [
            lambda ctx: {
                "defines": (ctx["children"][1], "lvl"),
                "uses": [(ctx["parent"], "lvl")],
                "fn": lambda _n, p_lvl: p_lvl + 1,
            },
            lambda ctx: {
                "defines": (ctx["children"][3], "lvl"),
                "uses": [(ctx["parent"], "lvl")],
                "fn": lambda _n, p_lvl: p_lvl,
            },
            lambda ctx: {
                "defines": (ctx["parent"], "cost"),
                "uses": [(ctx["children"][1], "cost"), (ctx["children"][3], "cost")],
                "fn": lambda _n, t_cost, b2_cost: t_cost + b2_cost,
            },
        ],
        ("B", "e"): [
            lambda ctx: {
                "defines": (ctx["parent"], "cost"),
                "uses": [],
                "fn": lambda _n: 0,
            },
        ],
        ("T", "dT"): [
            lambda ctx: {
                "defines": (ctx["children"][1], "lvl"),
                "uses": [(ctx["parent"], "lvl")],
                "fn": lambda _n, p_lvl: p_lvl,
            },
            lambda ctx: {
                "defines": (ctx["parent"], "cost"),
                "uses": [(ctx["parent"], "lvl"), (ctx["children"][1], "cost")],
                "fn": lambda _n, p_lvl, t2_cost: p_lvl * 2 + t2_cost,
            },
        ],
        ("T", "c"): [
            lambda ctx: {
                "defines": (ctx["parent"], "cost"),
                "uses": [(ctx["parent"], "lvl")],
                "fn": lambda _n, p_lvl: p_lvl,
            },
        ],
    }

    if circular:
        spec[("B", "e")] = [
            lambda ctx: {
                "defines": (ctx["parent"], "cost"),
                "uses": [(ctx["parent"], "lvl")],
                "fn": lambda _n, p_lvl: p_lvl,
            },
            lambda ctx: {
                "defines": (ctx["parent"], "lvl"),
                "uses": [(ctx["parent"], "cost")],
                "fn": lambda _n, b_cost: b_cost + 1,
            },
        ]

    return SDDEvaluator(spec, main_attr="cost")