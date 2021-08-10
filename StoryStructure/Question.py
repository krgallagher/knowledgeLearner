from StoryStructure.Statement import Statement


class Question(Statement):
    def __init__(self, text, lineId, answer=None, hints=None):
        Statement.__init__(self, text, lineId)
        for i in range(0, len(answer)):
            answer[i] = answer[i].lower()
        self.answer = answer
        self.hints = hints
        self.variableTypes = {}

    def getAnswer(self):
        return self.answer

    def setAnswer(self, answer):
        self.answer = answer

    def getHints(self):
        return self.hints

    def isCorrectAnswer(self, answer):
        if len(answer) >= 2 and self.isWhatQuestion():
            return {item.lower() in answer for item in answer} == {item.lower() in self.answer for item in self.answer}
            # return set(answer) == set(self.answer)
        for i in range(0, len(self.answer)):
            self.answer[i] = self.answer[i].lower()
        for j in range(0, len(answer)):
            answer[j] = answer[j].lower()
        return answer == self.answer

    def getQuestionWithAnswers(self, eventCalculusNeeded=True):
        questionWithAnswer = []
        for answer in self.getAnswer():
            example = self.answerFiller(answer, eventCalculusNeeded)
            questionWithAnswer.append(example)
        return questionWithAnswer

    def createPartialInterpretation(self, eventCalculusNeeded, answers=None):
        if self.isYesNoMaybeQuestion():
            if eventCalculusNeeded:
                representation = self.eventCalculusRepresentation[0][0]
            else:
                representation = self.getFluents().copy()[0][0]
            return '{' + representation + '}'
        interpretation = '{'
        for answer in answers:
            if answers.index(answer) != 0:
                interpretation += ','
            example = self.answerFiller(answer, eventCalculusNeeded)
            interpretation += example
        interpretation += '}'
        return interpretation

    # holdsAt(give(Bill,V1,Fred),1).
    # holdsAt(give(V1,football,Fred),1).

    # need to consider the scenario where the thing we want to fill in is the first in the representation
    def answerFiller(self, answer, eventCalculusNeeded):
        if eventCalculusNeeded:
            representation = self.getEventCalculusRepresentation()[0][0]
        else:
            representation = self.getFluents()[0][0]
        representationWithAnswer = representation.replace("V1", answer.lower())
        return representationWithAnswer

    def isYesNoMaybeQuestion(self):
        if self.answer:
            return "yes" in self.answer or "no" in self.answer or "maybe" in self.answer
        # need to get the token here.
        firstWord = self.doc[0].lemma_.lower()
        # TODO check for modal or auxiliary verbs (right now we are only checking for auxiliary verbs)
        return firstWord == "be" or firstWord == "do" or firstWord == "have"

    def isHowManyQuestion(self):
        return "how many" in self.text.lower()

    def isWhereQuestion(self):
        return "where" in self.text.lower()

    def isWhatQuestion(self):
        return "what" in self.text.lower()

    def isWhoQuestion(self):
        return "who" in self.text.lower()
