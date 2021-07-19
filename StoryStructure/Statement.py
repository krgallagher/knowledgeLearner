class Statement:
    def __init__(self, lineId, text):
        self.text = text
        self.lineId = int(lineId)
        self.fluent = None
        self.eventCalculusRepresentation = None
        self.modeBiasFluent = None
        self.predicates = set()
        self.eventCalculusPredicates = set()
        self.negatedVerb = False

        # create a time predicate for the event calculus representation
        time = "time(" + str(self.getLineID()) + ")"
        self.addEventCalculusPredicate(time)

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

    def addEventCalculusPredicate(self, predicate):
        self.eventCalculusPredicates.add(predicate)

    def getEventCalculusPredicates(self):
        return self.eventCalculusPredicates
