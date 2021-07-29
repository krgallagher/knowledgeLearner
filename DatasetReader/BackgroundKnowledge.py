def eventCalculusAxioms():
    axiom1 = "holdsAt(F,T+1) :- initiatedAt(F,T), time(T)."
    axiom2 = "holdsAt(F,T+1) :- holdsAt(F,T), not terminatedAt(F,T), time(T)."
    #will want to fix this later, but okay for now:
    axiom3 = "nn(nothing)."
    axioms: set[str] = set()
    axioms.add(axiom1)
    axioms.add(axiom2)
    axioms.add(axiom3)
    return axioms
