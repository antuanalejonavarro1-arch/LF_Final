"""Grafo de dependencias de un árbol de derivación (Aho et al., secciones 5.2.1 y 5.2.2).

Un vértice es un atributo concreto de un nodo del árbol: (id del nodo, nombre del atributo).
Hay una arista  u -> v  cuando el cálculo de v usa el valor de u.
"""
from collections import deque, namedtuple


class SDDError(Exception):
    """La SDD está mal definida (atributo definido dos veces, usado sin definir, etc.)."""


# Una regla semántica de una producción A -> X1 X2 ... Xn.
#   target: (posición, atributo) que la regla define
#   uses:   lista de (posición, atributo) que la regla necesita
#   fn:     función que recibe los valores de 'uses' (en ese orden) y devuelve el valor de 'target'
# Posición 0 = la cabeza A; posición i (1..n) = el símbolo Xi del cuerpo, igual que en el libro.
SemanticRule = namedtuple("SemanticRule", "target uses fn")


class DependencyGraph:
    def __init__(self, root, sdd_spec):
        self.nodes = {}      # id de nodo -> ParseNode
        self.values = {}     # (id, atributo) -> valor ya conocido (al inicio, solo los lexval)
        self.rule_of = {}    # (id, atributo) -> (vértices que usa, función que lo calcula)
        self.edges = {}      # vértice -> conjunto de vértices que dependen de él

        self._number_nodes(root)
        self._add_known_attributes()
        self._instantiate_rules(sdd_spec)
        self._check_all_used_attributes_are_defined()

    # ---------------------------------------------------------- construcción
    def _number_nodes(self, root):
        """Da a cada nodo un identificador n0, n1, ... (recorrido en preorden)."""
        def visit(node):
            node.node_id = f"n{len(self.nodes)}"
            self.nodes[node.node_id] = node
            for child in node.children:
                visit(child)
        visit(root)

    def _add_known_attributes(self):
        """Los terminales ya traen su lexval: son vértices sin dependencias."""
        for node_id, node in self.nodes.items():
            for attribute, value in node.attributes.items():
                self.values[(node_id, attribute)] = value
                self.edges.setdefault((node_id, attribute), set())

    def _instantiate_rules(self, sdd_spec):
        """Para cada nodo interno, copia las reglas de su producción sobre los nodos reales."""
        for node in self.nodes.values():
            if node.is_terminal:
                continue
            for rule in sdd_spec.get(node.production, []):
                self._instantiate_rule(node, rule)

    def _instantiate_rule(self, node, rule):
        positions = [node] + node.children       # posición 0 = el nodo, 1..n = sus hijos

        def vertex(position_and_attribute):
            position, attribute = position_and_attribute
            if position >= len(positions):
                raise SDDError(f"rule of {node.production} uses position {position}, "
                               f"which does not exist in the production")
            return (positions[position].node_id, attribute)

        target = vertex(rule.target)
        if target in self.rule_of or target in self.values:
            raise SDDError(f"attribute {target[1]} of node {target[0]} is defined twice")
        sources = [vertex(use) for use in rule.uses]

        self.rule_of[target] = (sources, rule.fn)
        self.edges.setdefault(target, set())
        for source in sources:
            # Arista source -> target: primero se evalúa 'source' y luego 'target'.
            self.edges.setdefault(source, set()).add(target)

    def _check_all_used_attributes_are_defined(self):
        for node_id, attribute in self.edges:
            if (node_id, attribute) not in self.rule_of and (node_id, attribute) not in self.values:
                raise SDDError(f"attribute {attribute} of node {node_id} is used but never defined")

    # ---------------------------------------------------------- orden de evaluación
    def topological_order(self):
        """Orden topológico (algoritmo de Kahn). Devuelve None si el grafo tiene un ciclo."""
        in_degree = {vertex: 0 for vertex in self.edges}
        for targets in self.edges.values():
            for target in targets:
                in_degree[target] += 1

        ready = deque(v for v, degree in in_degree.items() if degree == 0)
        order = []
        while ready:
            vertex = ready.popleft()
            order.append(vertex)
            for target in sorted(self.edges[vertex]):
                in_degree[target] -= 1
                if in_degree[target] == 0:
                    ready.append(target)

        return order if len(order) == len(self.edges) else None   # sobran vértices => hay ciclo
