from StoryStructure.Statement import Statement


class Question(Statement):
    def __init__(self, text, lineId, answer, hints):
        Statement.__init__(self, text, lineId)
        self.answer = answer  # this should be stored as a list
        self.hints = hints

    def getAnswer(self):
        return self.answer

    def getHints(self):
        return self.hints

    #TODO might want to fix this so that order does/does not matter when the size is greater than 1 for the answer set
    def isCorrectAnswer(self, answer):
        return answer == self.answer

    def getQuestionWithAnswers(self, eventCalculusNeeded=True):
        questionWithAnswer = []
        for answer in self.getAnswer():
            example = self.answerFiller(answer, eventCalculusNeeded)
            questionWithAnswer.append(example)
        return questionWithAnswer

    def createPartialInterpretation(self, answers, eventCalculusNeeded):
        if self.isYesNoQuestion():
            if eventCalculusNeeded:
                representation = self.eventCalculusRepresentation.copy().pop()
            else:
                representation = self.getFluents().copy().pop()
            return '{' + representation + '}'
        interpretation = '{'
        for answer in answers:
            if answers.index(answer) != 0:
                interpretation += ','
            example = self.answerFiller(answer, eventCalculusNeeded)
            interpretation += example
        interpretation += '}'
        return interpretation

    # might be able to fill this according to the representation I want...
    def answerFiller(self, answer, eventCalculusNeeded):
        if eventCalculusNeeded:
            representation = self.getEventCalculusRepresentation().copy()
        else:
            representation = self.getFluents().copy()
        representation = representation.pop()
        splitting = representation.split(',')
        for i in range(0, len(splitting)):
            if splitting[i][0] == 'V':
                splitting[i] = answer + ')'
        example = ''
        for element in splitting:
            if example:
                example += ','
            example += element
        return example

    def isYesNoQuestion(self):
        return "yes" in self.answer or "no" in self.answer