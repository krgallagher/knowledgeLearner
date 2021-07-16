class Statement:
    def __init__(self, lineId, text):
        self.text = text
        self.lineId = int(lineId)
        # perhaps should save the fluents and have a separate fluents and then partialASP program with event calculus?
        self.fluent = None  # will eventually want this to be a set
        self.eventCalculusRepresentation = None
        self.modeBiasFluent = None
        self.predicates = set()
        self.negatedVerb = False

    def __eq__(self, other):
        return self.text == other.text and self.lineId == other.lineId

    def getText(self):
        return self.text

    def getLineID(self):
        return self.lineId

    def getFluent(self):
        return self.fluent

    def getEventCalculusRepresentation(self):
        return self.eventCalculusRepresentation

    def setEventCalculusRepresentation(self, representation):
        self.eventCalculusRepresentation = representation

    def setFluent(self, fluent):
        self.fluent = fluent

    def setModeBiasFluent(self, modeBiasFluent):
        self.modeBiasFluent = modeBiasFluent

    def getModeBiasFluent(self):
        return self.modeBiasFluent

    def addPredicate(self, predicate):
        self.predicates.add(predicate)

    def getPredicates(self):
        return self.predicates
