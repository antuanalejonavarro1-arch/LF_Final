# LF_Final — Formal Languages Project

Implementation of the Formal Languages project (FIRST/FOLLOW sets, LL(1) and SLR(1) parsers, and a syntax-directed definition evaluator), following Aho et al., *Compilers: Principles, Techniques, and Tools* (2nd edition), sections 4.4, 4.5, 4.6, 5.1 and 5.2.

## Group members

- Antuan Alejandro Navarro Ortiz
- Carlos Mario Monsalve Tangarife
- Daniel Felipe Serna Medina

## Environment

| Item | Version |
|---|---|
| Operating system | Windows 11 Pro |
| Programming language | Python 3.13.14 |
| Editor | Visual Studio Code |
| External libraries | None (Python standard library only) |

No parser generators, parsing libraries, or libraries that compute First/Follow sets, LR automata or parsing tables are used.

## Repository structure

```
LF_Final/
├── main.py                  Entry point (reads the grammar and the strings from stdin)
├── src/
│   ├── grammar.py           Grammar reading, terminals, tokenization
│   ├── first_follow.py      FIRST and FOLLOW sets (Sec. 4.4.2)
│   ├── ll1_parser.py        LL(1) table and table-driven predictive parser (Sec. 4.4.3-4.4.4)
│   ├── lr0_automaton.py     LR(0) items, CLOSURE, GOTO, canonical collection (Sec. 4.6.2)
│   ├── slr1_parser.py       SLR(1) ACTION/GOTO tables and LR parser (Sec. 4.6.3-4.6.4)
│   ├── parse_tree.py        Parse tree node shared by both parsers
│   ├── dependency_graph.py  Dependency graph and topological order (Sec. 5.2.1-5.2.2)
│   ├── sdd_evaluator.py     Generic SDD evaluator
│   └── sample_sdd.py        The SDD used in Item 3, written as data
└── tests/
    ├── run_tests.py         Automatic smoke tests
    └── *.txt                Example input files (see below)
```

## Requirements

Python 3 (developed and run with Python 3.13.14). Nothing else needs to be installed.

## Input format

The grammar is read from standard input, followed by the strings to parse (one per line):

```
<n>                                   number of nonterminals
<nonterminal> -> <alternatives separated by blank spaces>
... (n lines)
<string 1>
<string 2>
...
<empty line>                          ends the list of strings
```

Conventions: `S` is the start symbol, nonterminals are capital letters, `e` is the empty string (ε), and `$` is the end marker (appended by the program; it must not appear in the input strings). The empty string is given as a line containing only `e`.

Example (`tests/ejm1.txt`):

```
3
S -> S+T T
T -> T*F F
F -> (S) i
i+i
(i)
(i+i)*i)

```

## How to run Items 1 and 2 (First/Follow, LL(1), SLR(1))

Run from the repository root, redirecting a file to standard input.

**Windows PowerShell** (the `<` operator is not supported):

```powershell
Get-Content tests\ejm1.txt | python3 main.py
```

**Windows cmd, Linux, macOS:**

```
python3 main.py < tests/ejm1.txt
```

(On Windows `cmd`, use `python` and backslashes in the path if `python3` is not available.)

You can also run `python3 main.py` and type the grammar and the strings by hand, ending the strings with an empty line.

### Behavior

The program decides whether the grammar is LL(1) and/or SLR(1):

| Grammar | Output |
|---|---|
| LL(1) and SLR(1) | `Select a parser (T: for LL(1), B: for SLR(1), Q: quit):`, then strings are parsed with the chosen parser (`yes`/`no` per string, until an empty line); the query is printed again; `Q` ends the program |
| LL(1) only | `Grammar is LL(1).` and then `yes`/`no` per string |
| SLR(1) only | `Grammar is SLR(1).` and then `yes`/`no` per string |
| Neither | `Grammar is neither LL(1) nor SLR(1).` and the program finishes |

### Optional flags

| Flag | Effect |
|---|---|
| `--sets` | Prints `First(A) = {...}` and `Follow(A) = {...}` for each nonterminal (alphabetical order; terminals in ASCII order, then `e`, then `$`) before continuing |
| `--table` | Prints the LL(1) table (if the grammar is LL(1)), the LR(0) automaton and the SLR(1) table |
| `--trace` | Prints the stack step by step for every parsed string |

Examples:

```powershell
Get-Content tests\ejm2.txt | python3 main.py --sets
Get-Content tests\ejm2.txt | python3 main.py --table
Get-Content tests\ejm1.txt | python3 main.py --trace
```

## How to run Item 3 (syntax-directed definition)

Item 3 uses the same grammar input format and the flag `--sdd`. The strings are parsed with the SLR(1) parser (or the LL(1) parser if the grammar is not SLR(1)), the parse tree is built, and the attributes are evaluated with the dependency-graph method (dependency graph, topological order, evaluation in that order).

The SDD is defined in `src/sample_sdd.py` as data (a list of semantic rules per production). It is used with the grammar:

```
S -> B
B -> [T]B e
T -> dT c x
```

Attributes: `lvl` (inherited, on `B` and `T`) and `cost` (synthesized, on `S`, `B` and `T`). The main attribute is `S.cost`.

```powershell
Get-Content tests\sdd.txt | python3 main.py --sdd
```

For every string, the program prints `no` if the string is not in the language; otherwise it prints the annotated parse tree (one node per line, indented by depth), the evaluation order, and `Result (cost): N`.

To show the detection of circular definitions, the flag `--circular` replaces one rule of the SDD by a circular one:

```powershell
Get-Content tests\sdd.txt | python3 main.py --sdd --circular
```

When a circular dependency is found, the program prints `SDD is circular` and stops.

Expected results with `tests/sdd.txt`: `e` gives `Result (cost): 0`, `[c]` gives `2`, `[dc][x]` gives `12`, and `[d]` and `c` give `no`.

## Tests

Run from the repository root:

```
python3 tests/run_tests.py
```

The script runs the three examples of the assignment, the `--sets` output, the SDD evaluation and the circular-SDD detection. All lines must start with `PASS`.

Example input files in `tests/` (they can be used as shown above):

| File | Grammar case |
|---|---|
| `ejm1.txt` | SLR(1) but not LL(1) |
| `ejm2.txt` | LL(1) and SLR(1) (uses the parser menu) |
| `ejm3.txt` | neither LL(1) nor SLR(1) |
| `ejm4.txt` | LL(1) but not SLR(1) |
| `sdd.txt` | grammar and strings for Item 3 |

## Book sections followed

| Part | Book reference |
|---|---|
| FIRST and FOLLOW | Section 4.4.2 |
| LL(1) table and predictive parser | Sections 4.4.3 and 4.4.4 (Algorithm 4.31) |
| LR(0) items, CLOSURE, GOTO | Section 4.6.2 |
| LR parsing algorithm | Section 4.6.3 |
| SLR(1) ACTION/GOTO tables | Section 4.6.4 |
| Dependency graph and evaluation order | Sections 5.2.1 and 5.2.2 |
| SDD classification (S-/L-attributed) | Sections 5.2.3 and 5.2.4 |

## Use of generative AI

We used generative AI tools as a support, not as a replacement for reading the book or for the hand-worked examples:

- **Claude** and **Gemini**.
- Purposes: clarifying concepts, finding errors, reviewing the code, and studying the code together with the AI tools to improve our understanding of it.
- Code comments: most of the comments in the source code were written by the AI tools so that we could find our way around the code more easily.

We are responsible for everything we submit.
