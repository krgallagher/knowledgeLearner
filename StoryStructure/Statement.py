class Statement:
    def __init__(self, lineId, text):
        self.text = text
        self.lineId = int(lineId)
        self.fluents = list(list())
        self.eventCalculusRepresentation = list(list())
        self.modeBiasFluents = list(list())
        self.staticPredicates = set()  # might want to rename this to something else
        self.negatedVerb = False
        self.doc = None  # maybe initialise this in the parser?

    def __eq__(self, other):
        return self.text == other.text and self.lineId == other.lineId

    def getText(self):
        return self.text

    def getLineID(self):
        return self.lineId

    def getEventCalculusRepresentation(self):
        return self.eventCalculusRepresentation

    def setEventCalculusRepresentation(self, representation):
        self.eventCalculusRepresentation = representation

    def setFluents(self, fluents):
        self.fluents = fluents

    def getFluents(self):
        return self.fluents

    def setModeBiasFluents(self, modeBiasFluents):
        self.modeBiasFluents = modeBiasFluents

    def getModeBiasFluents(self):
        return self.modeBiasFluents

    def addPredicate(self, predicate):
        self.staticPredicates.add(predicate)

    def getPredicates(self):
        return self.staticPredicates
