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