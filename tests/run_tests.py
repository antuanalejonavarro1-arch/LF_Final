"""Smoke tests: python3 tests/run_tests.py  (run from the repository root)."""
import subprocess, sys

def run(stdin, *flags):
    r = subprocess.run([sys.executable, "main.py", *flags], input=stdin, capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip().splitlines()

G_SDD = "3\nS -> B\nB -> [T]B e\nT -> dT c x\n"
CASES = [
    ("Example 1 (SLR only)", "3\nS -> S+T T\nT -> T*F F\nF -> (S) i\ni+i\n(i)\n(i+i)*i)\n\n", [],
     ["Grammar is SLR(1).", "yes", "yes", "no"]),
    ("Example 2 (both parsers)", "3\nS -> AB\nA -> aA d\nB -> bBc e\nT\nd\nadbc\na\n\nB\nd\nadbc\na\n\nQ\n", [],
     ["Select a parser (T: for LL(1), B: for SLR(1), Q: quit):", "yes", "yes", "no"] * 1
     + ["Select a parser (T: for LL(1), B: for SLR(1), Q: quit):", "yes", "yes", "no",
        "Select a parser (T: for LL(1), B: for SLR(1), Q: quit):"]),
    ("Example 3 (neither)", "1\nS -> SS a\n", [], ["Grammar is neither LL(1) nor SLR(1)."]),
    ("BOM in first line", "\ufeff1\nS -> a\na\n\n", [], None),
    ("--sets format", "3\nS -> AB\nA -> aA d\nB -> bBc e\n", ["--sets"],
     ["First(A) = {a, d}", "Follow(A) = {b, $}", "First(B) = {b, e}", "Follow(B) = {c, $}",
      "First(S) = {a, d}", "Follow(S) = {$}"]),
]
fail = 0
for name, inp, flags, exp in CASES:
    out = run(inp, *flags)
    ok = True if exp is None else (out[:len(exp)] == exp if flags else out == exp)
    if name.startswith("BOM"):
        ok = bool(out) and out[0].startswith("Select a parser")
    print(("PASS " if ok else "FAIL ") + name); fail += not ok
    if not ok: print("  got:", out)

# SDD: (string, expected value of S.cost) ; None -> "no"
SDD = [("e", 0), ("[c]", 2), ("[x]", 6), ("[dc]", 6), ("[dc][x]", 12), ("[c][c][c][c][c][c]", 12), ("[d]", None), ("c", None)]
out = run(G_SDD + "\n".join(s for s, _ in SDD) + "\n\n", "--sdd")
vals = [l for l in out if l.startswith("Result") or l == "no"]
exp = [("no" if v is None else f"Result (cost): {v}") for _, v in SDD]
ok = vals == exp; print(("PASS " if ok else "FAIL ") + "SDD values"); fail += not ok
if not ok: print("  got:", vals)
out = run(G_SDD + "[dc]\n\n", "--sdd", "--circular")
ok = out == ["SDD is circular"]; print(("PASS " if ok else "FAIL ") + "SDD circular detection"); fail += not ok
sys.exit(1 if fail else 0)
