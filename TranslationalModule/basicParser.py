import spacy
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Story
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import holdsAt, happensAt, initiatedAt, terminatedAt, EventCalculusWrapper


def modeHWrapping(predicate):
    return "#modeh(" + predicate + ")."


def modeBWrapping(predicate):
    return "#modeb(" + predicate + ")."


def varWrapping(tag):
    return "var(" + tag + ")"


def generateNonBeBias(modeBiasFluent):
    bias = set()
    time = varWrapping("time")
    happens = happensAt(modeBiasFluent, time)
    bias.add(modeBWrapping(happens))
    return bias


def generateBeBias(modeBiasFluent):
    bias = set()
    time = varWrapping("time")
    initiated = initiatedAt(modeBiasFluent, time)
    holds = holdsAt(modeBiasFluent, time)
    terminated = terminatedAt(modeBiasFluent, time)
    bias.add(modeHWrapping(initiated))
    bias.add(modeBWrapping(holds))
    bias.add(modeHWrapping(terminated))
    return bias


def timePredicate(statement: Statement):
    time = "time(" + str(statement.getLineID()) + ")"
    return time


def formStatementFluent(statement: Statement, fluent, modeBiasFluent, root):
    children = root.children
    for child in children:
        tag = child.tag_.lower()
        lemma = child.lemma_.lower()
        if 'nn' in tag:
            if not fluent[-1] == '(':
                fluent += ','
                modeBiasFluent += ','
            fluent += lemma
            modeBiasFluent += varWrapping(tag)
            # add tag predicates
            relevantPredicate = tag + '(' + lemma + ')'
            statement.addPredicate(relevantPredicate)
        fluent, modeBiasFluent = formStatementFluent(statement, fluent, modeBiasFluent, child)
    return fluent, modeBiasFluent


def formQuestionFluent(question: Question, fluent, modeBiasFluent, root):
    children = root.children
    for child in children:
        tag = child.tag_.lower()
        lemma = child.lemma_.lower()
        if 'nn' in tag:
            if not fluent[-1] == '(':
                fluent += ','
            fluent += lemma
            modeBiasFluent += varWrapping(tag)
            # add tag predicates
            relevantPredicate = tag + '(' + lemma + ')'
            question.addPredicate(relevantPredicate)
        fluent, modeBiasFluent = formStatementFluent(question, fluent, modeBiasFluent, child)
    if not fluent[-1] == '(':
        fluent += ','
        modeBiasFluent += ','
    fluent += "V1"
    modeBiasFluent += varWrapping('nn')
    # might want to add multiple options here
    return fluent, modeBiasFluent



class BasicParser:
    def __init__(self, corpus):
        self.nlp = spacy.load("en_core_web_sm")
        self.synonymDictionary = {}
        self.previousQuestionIndex = -1
        self.conceptNet = ConceptNetIntegration()
        self.eventCalculusWrapper = EventCalculusWrapper()
        self.conceptsToExplore = set()
        self.corpus = corpus

    def parse(self, story: Story, statement: Statement):
        if isinstance(statement, Question):
            self.parseQuestion(statement, story)
        else:
            self.parseStatement(statement)
        statement.addPredicate(timePredicate(statement))

    def parseStatement(self, statement: Statement):
        doc = self.nlp(statement.getText())
        fluent = ""
        root = [token for token in doc if token.head == token][0]
        adposition = [token for token in doc if token.pos_ == "ADP"]
        fluent += root.lemma_
        if adposition:
            fluent += '_' + adposition[0].text
        conceptsToExplore = set()
        conceptsToExplore.add(fluent)
        fluent += "("
        modeBiasFluent = fluent
        fluent, modeBiasFluent = formStatementFluent(statement, fluent, modeBiasFluent, root)
        fluent += ")"
        modeBiasFluent += ")"
        statement.setFluent(fluent)
        statement.setModeBiasFluent(modeBiasFluent)
        self.conceptsToExplore.update(conceptsToExplore)

    def parseQuestion(self, question: Question, story: Story):
        doc = self.nlp(question.getText())
        fluent = ""
        root = [token for token in doc if token.head == token][0]
        fluent += root.lemma_
        fluent += "("
        modeBiasFluent = fluent
        fluent, modeBiasFluent = formQuestionFluent(question, fluent, modeBiasFluent, root)
        fluent += ")"
        modeBiasFluent += ')'
        question.setFluent(fluent)
        question.setModeBiasFluent(modeBiasFluent)
        self.synonymChecker(self.conceptsToExplore)
        self.updateFluents(story, question)
        self.setEventCalculusRepresentation(story, question)
        index = story.getIndex(question)
        if index + 1 == story.size():
            self.previousQuestionIndex = -1
        else:
            self.previousQuestionIndex = index

    def updateFluents(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            fluent = currentStatement.getFluent()
            modeBiasFluent = currentStatement.getModeBiasFluent()
            currentStatement.setFluent(self.update(fluent))
            currentStatement.setModeBiasFluent(self.update(modeBiasFluent))

    def update(self, fluent):
        splitFluent = fluent.split('(')
        predicate = splitFluent[0]
        if predicate in self.synonymDictionary.keys():
            updatedFluent = self.synonymDictionary[predicate]
        else:
            return fluent
        if len(splitFluent) == 1:
            return updatedFluent
        for index in range(1, len(splitFluent)):
            updatedFluent += '(' + splitFluent[index]
        return updatedFluent

    def setEventCalculusRepresentation(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            fluent = currentStatement.getFluent()
            modeBiasFluent = currentStatement.getModeBiasFluent()
            self.eventCalculusWrapper.wrap(currentStatement)
            predicate = fluent.split('(')[0]
            if predicate == "be":
                modeBias = generateBeBias(modeBiasFluent)
            else:
                modeBias = generateNonBeBias(modeBiasFluent)
            self.corpus.updateModeBias(modeBias)

    def checkCurrentSynonyms(self, concept):
        for value in self.synonymDictionary.values():
            if self.conceptNet.isSynonym(concept, value):
                self.synonymDictionary[concept] = value
                return True
        for key in self.synonymDictionary.values():
            if self.conceptNet.isSynonym(concept, key):
                self.synonymDictionary[concept] = self.synonymDictionary[key]
        return False

    def synonymChecker(self, concepts):
        conceptsCopy = concepts.copy()
        for concept in conceptsCopy:
            if concept in self.synonymDictionary.keys():
                concepts.remove(concept)
            elif concept in self.synonymDictionary.values():
                self.synonymDictionary[concept] = concept
                concepts.remove(concept)
            elif self.checkCurrentSynonyms(concept):
                concepts.remove(concept)
        learnedConcepts = self.conceptNet.synonymFinder(concepts)
        self.synonymDictionary.update(learnedConcepts)


if __name__ == '__main__':
    # process data
    # reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")

    # get corpus
    corpus = reader.corpus

    # initialise parser
    parser = BasicParser(corpus)

    for story in reader.corpus:
        for sentence in story:
            parser.parse(story, sentence)
        for sentence in story:
            print(sentence.getText(), sentence.getLineID(), sentence.getFluent(),
                  sentence.getEventCalculusRepresentation())
    print(corpus.modeBias)
    print(parser.synonymDictionary)
