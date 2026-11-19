"""La SDD que usa el Ítem 3, escrita como DATOS (una lista de reglas por producción).

Gramática:   S -> B        B -> [T]B | e        T -> dT | c | x

Atributos:
  lvl  (heredado,    en B y T) : nivel/peso con que aparece el símbolo
  cost (sintetizado, en S, B y T) : costo acumulado del subárbol; es el atributo principal (S.cost)

Posiciones en cada regla: 0 = cabeza; 1..n = símbolos del lado derecho, de izquierda a derecha.
"""
from src.dependency_graph import SemanticRule as Rule
from src.sdd_evaluator import SDDEvaluator


def build_sample_sdd(circular=False):
    spec = {
        # S -> B          B.lvl = 1 ;  S.cost = B.cost
        ("S", "B"): [
            Rule((1, "lvl"), [], lambda: 1),
            Rule((0, "cost"), [(1, "cost")], lambda b_cost: b_cost),
        ],
        # B -> [ T ] B1   (posiciones: '['=1, T=2, ']'=3, B1=4)
        #   T.lvl = B.lvl + 1 ;  B1.lvl = B.lvl ;  B.cost = T.cost + B1.cost
        ("B", "[T]B"): [
            Rule((2, "lvl"), [(0, "lvl")], lambda b_lvl: b_lvl + 1),
            Rule((4, "lvl"), [(0, "lvl")], lambda b_lvl: b_lvl),
            Rule((0, "cost"), [(2, "cost"), (4, "cost")], lambda t_cost, b1_cost: t_cost + b1_cost),
        ],
        # B -> e          B.cost = 0
        ("B", "e"): [
            Rule((0, "cost"), [], lambda: 0),
        ],
        # T -> d T1       T1.lvl = T.lvl ;  T.cost = 2*T.lvl + T1.cost
        ("T", "dT"): [
            Rule((2, "lvl"), [(0, "lvl")], lambda t_lvl: t_lvl),
            Rule((0, "cost"), [(0, "lvl"), (2, "cost")], lambda t_lvl, t1_cost: 2 * t_lvl + t1_cost),
        ],
        # T -> c          T.cost = T.lvl
        ("T", "c"): [
            Rule((0, "cost"), [(0, "lvl")], lambda t_lvl: t_lvl),
        ],
        # T -> x          T.cost = 3*T.lvl
        ("T", "x"): [
            Rule((0, "cost"), [(0, "lvl")], lambda t_lvl: 3 * t_lvl),
        ],
    }

    if circular:
        # Demostración de circularidad: se cambia UNA regla de T -> dT.
        # Ahora T1.lvl = T1.cost + 1, pero T1.cost depende de T1.lvl  =>  ciclo (p. ej. con "[dc]").
        spec[("T", "dT")][0] = Rule((2, "lvl"), [(2, "cost")], lambda t1_cost: t1_cost + 1)

    return SDDEvaluator(spec, main_attr="cost")
