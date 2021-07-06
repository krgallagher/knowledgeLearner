class Statement:
    def __init__(self, lineId, text):
        self.text = text
        self.lineId = lineId
        self.logicalRepresentation = None

    def getText(self):
        return self.text

    def getLineID(self):
        return self.lineId

    def getLogicalRepresentation(self):
        return self.logicalReprentation


