import spacy


# might need to store timestamp with the fluents being created.
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


def generateBeBias(fluent):
    pass
    # replace all of the arguments of the fluent with unique variable names
    # put it in place the correct event calculus wrappers


def generateNonBeBias(fluent):
    pass


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
                if predicate.text == "be":
                    modeBias.update(generateBeBias(fluent))
                else:
                    modeBias.update(generateNonBeBias(fluent))
        return modeBias



