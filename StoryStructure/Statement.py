class Statement:
    def __init__(self, lineId, text):
        self.text = text
        self.lineId = lineId
        # perhaps should save the fluents and have a separate fluents and then partialASP program with event calculus?
        self.fluent = None  # will eventually want this to be a set
        self.eventCalculusRepresentation = None
        self.predicates = set()  # may want to change this name later on, need to read more about the event calculus

    def getText(self):
        return self.text

    def getLineID(self):
        return self.lineId

    def getFluent(self):
        return self.fluent

    def getEventCalculusRepresentation(self):
        return self.eventCalculusRepresentation

    def getPredicates(self):
        return self.predicates

    def setEventCalculusRepresentation(self, representation):
        self.eventCalculusRepresentation = representation

    def setFluent(self, fluent):
        self.fluent = fluent

    def setPredicates(self, predicates):
        self.predicates.update(predicates)
