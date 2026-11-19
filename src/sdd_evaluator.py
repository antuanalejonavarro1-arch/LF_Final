"""Evaluador general de una SDD sobre un árbol de derivación (Aho et al., sección 5.2).

No sabe nada de una SDD en particular: recibe las reglas como datos (ver sample_sdd.py).
Pasos: construir el grafo de dependencias -> ordenarlo topológicamente -> evaluar en ese orden.
"""
from src.dependency_graph import DependencyGraph, SDDError


class SDDEvaluator:
    def __init__(self, sdd_spec, main_attr):
        self.sdd_spec = sdd_spec      # dict: (lhs, alternativa) -> lista de SemanticRule
        self.main_attr = main_attr    # atributo de S que se reporta como resultado

    def check_against_grammar(self, grammar):
        """Toda producción de la gramática debe tener su entrada en la SDD."""
        missing = [f"{lhs}->{alt}" for lhs, alt in grammar.all_productions()
                   if (lhs, alt) not in self.sdd_spec]
        if missing:
            raise SDDError("SDD has no rules for productions: " + ", ".join(missing))

    def evaluate_tree(self, root):
        """Evalúa todos los atributos del árbol.

        Devuelve {"circular": True} si el grafo tiene un ciclo; si no, un dict con el
        orden de evaluación y el valor del atributo principal de la raíz.
        """
        graph = DependencyGraph(root, self.sdd_spec)
        order = graph.topological_order()
        if order is None:
            return {"circular": True}

        order_labels = []
        for vertex in order:
            node_id, attribute = vertex
            node = graph.nodes[node_id]
            order_labels.append(f"{node.symbol}({node_id}).{attribute}")

            if vertex in graph.rule_of:          # los lexval no se calculan: ya tienen valor
                sources, function = graph.rule_of[vertex]
                value = function(*[graph.values[source] for source in sources])
                graph.values[vertex] = value
                node.attributes[attribute] = value   # se guarda en el nodo dueño del atributo

        return {
            "circular": False,
            "order": order_labels,
            "root_value": graph.values.get((root.node_id, self.main_attr)),
        }

    def format_annotated_tree(self, root):
        """Árbol anotado: un nodo por línea, con sangría según la profundidad."""
        lines = []

        def visit(node, depth):
            attributes = ", ".join(f"{k}={v}" for k, v in sorted(node.attributes.items()))
            production = f" [{node.production[0]}->{node.production[1]}]" if node.production else ""
            lines.append(f"{'  ' * depth}{node.symbol}{production} {{{attributes}}}")
            for child in node.children:
                visit(child, depth + 1)

        visit(root, 0)
        return "\n".join(lines)
