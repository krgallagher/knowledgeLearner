import spacy
from TranslationalModule.EventCalculus import holdsAt, happensAt, initiatedAt, terminatedAt


def formStatementFluent(fluent, root):
    children = root.children
    for child in children:
        partOfSpeech = child.tag_
        if 'NN' in partOfSpeech:
            if not fluent[-1] == '(':
                fluent += ','
            fluent += child.lemma_.lower()
        fluent = formStatementFluent(fluent, child)
    return fluent


# very ad-hoc
def formQuestionFluent(fluent, root):
    children = root.children
    for child in children:
        partOfSpeech = child.tag_
        if 'NN' in partOfSpeech:
            if not fluent[-1] == '(':
                fluent += ','
            fluent += child.lemma_.lower()
        fluent = formStatementFluent(fluent, child)
    children = root.children
    if not fluent[-1] == '(':
        fluent += ','
    fluent += "V1"
    return fluent


def getRange(previousQuestion, statement, statements):
    statementIndex = statements.index(statement)
    previousQuestionIndex = 0
    if previousQuestion:
        previousQuestionIndex = statements.index(previousQuestion)
    return previousQuestionIndex, statementIndex


def giveUniqueVariableNames(fluent):
    fluentSplitting = fluent.split('(')
    predicate = fluentSplitting[0]
    arguments = fluentSplitting[1].split(',')

    newFluent = predicate + "("
    for i in range(0, len(arguments)):
        if not newFluent[-1] == '(':
            newFluent += ','
        newFluent += "var(t)"
    newFluent += ")"
    return newFluent


class BasicParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def parseStatement(self, statement):
        doc = self.nlp(statement.getText())
        fluent = ""
        root = [token for token in doc if token.head == token][0]
        fluent += root.lemma_
        fluent += "("
        fluent = formStatementFluent(fluent, root)
        fluent += ")"
        return fluent, [root.lemma_]

    def parseQuestion(self, question):
        doc = self.nlp(question.getText())
        fluent = ""
        root = [token for token in doc if token.head == token][0]
        fluent += root.lemma_
        fluent += "("
        fluent = formQuestionFluent(fluent, root)
        fluent += ")"
        return fluent, [root.lemma_]

    def generateModeBias(self, statements, statement, previousQuestion):
        modeBias = set()
        previousQuestionIndex, statementIndex = getRange(previousQuestion, statement, statements)
        for index in range(previousQuestionIndex, statementIndex):
            fluent = statements[index].getFluent()
            if fluent:
                predicate = fluent.split('(')[0]
                if predicate == "be":
                    modeBias.update(self.generateBeBias(fluent))
                else:
                    modeBias.update(self.generateNonBeBias(fluent))
        return modeBias

    def generateBeBias(self, fluent):
        generalisedFluent = giveUniqueVariableNames(fluent)
        bias = set()
        time = "var(time)"
        initiated = initiatedAt(generalisedFluent, time)
        holds = holdsAt(generalisedFluent, time)
        terminated = terminatedAt(generalisedFluent, time)
        bias.add(self.modehWrapping(initiated))
        bias.add(self.modehWrapping(holds))
        bias.add(self.modebWrapping(terminated))
        return bias

    def generateNonBeBias(self, fluent):
        generalisedFluent = giveUniqueVariableNames(fluent)
        bias = set()
        time = "var(time)"
        happens = happensAt(generalisedFluent, time)
        bias.add(self.modebWrapping(happens))
        return bias

    def modehWrapping(self, predicate):
        return "#modeh(" + predicate + ")."

    def modebWrapping(self, predicate):
        return "#modeb(" + predicate + ")."
