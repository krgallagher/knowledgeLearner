class Statement:
    def __init__(self, lineId, text):
        self.text = text
        self.lineId = lineId
        #perhaps should save the fluents and have a separate fluents and then partialASP program with event calculus?
        self.fluent = None
        self.eventCalculusRepresentation = None

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


