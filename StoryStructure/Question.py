from StoryStructure.Statement import Statement


class Question(Statement):
    def __init__(self, text, lineId, answer, hints):
        Statement.__init__(self, text, lineId)
        self.answer = answer
        self.hints = hints

    def getAnswer(self):
        return self.answer

    def isCorrectAnswer(self, answer):
        return answer == self.answer

    def createPartialInterpretation(self, answer, eventCalculusNeeded):
        if eventCalculusNeeded:
            representation = self.getEventCalculusRepresentation()
        else:
            representation = self.getFluent()
        splitting = representation.split(',')
        for i in range(0, len(splitting)):
            if splitting[i][0] == 'V':
                print(answer)
                splitting[i] = answer + ')'
        example = '{'
        for element in splitting:
            if not example == '{':
                example += ','
            example += element
        example += '}'
        return example

# might be able to drop the hints since they aren't very helpful
