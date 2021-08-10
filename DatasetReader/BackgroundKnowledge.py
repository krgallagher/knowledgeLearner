def eventCalculusAxioms():
    axiom1 = "holdsAt(F,T+1) :- initiatedAt(F,T), time(T)."
    axiom2 = "holdsAt(F,T+1) :- holdsAt(F,T), not terminatedAt(F,T), time(T)."
    # will want to fix this later, but okay for now:
    axioms: set[str] = set()
    axioms.add(axiom1)
    axioms.add(axiom2)
    return axioms
