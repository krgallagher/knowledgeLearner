def eventCalculusAxioms():
    axiom1 = "holdsAt(F,T+1) :- initiatedAt(F,T), time(T)."
    axiom2 = "holdsAt(F,T+1) :- holdsAt(F,T), not terminatedAt(F,T), time(T)."
    # axiom3 = "holdsAt(be_color(P,C),T) :- holdsAt(be(P,A),T), initiatedAt(be(P1,A),T1), holdsAt(color(P1,C),T), not initiatedAt(be(P2,A),T2), T1 < T2, T2 < T, P2 != P, npp(P2)."
    # will want to fix this later, but okay for now:
    axioms: set[str] = set()
    axioms.add(axiom1)
    axioms.add(axiom2)
    # axioms.add(axiom3)
    return axioms
