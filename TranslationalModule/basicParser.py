import spacy
from StoryStructure import Story
from StoryStructure.Question import Question
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import holdsAt, happensAt, initiatedAt, terminatedAt, EventCalculusWrapper


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

def formQuestionFluent(fluent, root):
    children = root.children
    for child in children:
        partOfSpeech = child.tag_
        if 'NN' in partOfSpeech:
            if not fluent[-1] == '(':
                fluent += ','
            fluent += child.lemma_.lower()
        fluent = formStatementFluent(fluent, child)
    if not fluent[-1] == '(':
        fluent += ','
    fluent += "V1"
    return fluent


# TODO combine the getRange function into a helper functions or utilities module
def getRange(question, statement, story):
    statementIndex = story.getIndex(statement)
    try:
        questionIndex = story.getIndex(question)
    except:
        questionIndex = 0
    return questionIndex, statementIndex


# TODO fix the mode bias generation so that it relies more on part of speech rather than being arbitrary
def giveUniqueVariableNames(fluent):
    fluentSplitting = fluent.split('(')
    predicate = fluentSplitting[0]
    arguments = fluentSplitting[1].split(',')
    # need to fix this later
    newFluent = predicate + "("
    newFluent += 'var(t),var(s)'
    '''
    for i in range(0, len(arguments)):
        if not newFluent[-1] == '(':
            newFluent += ','
        newFluent += "var(t)"
    '''
    newFluent += ")"
    return newFluent


def modeHWrapping(predicate):
    return "#modeh(" + predicate + ")."


def modeBWrapping(predicate):
    return "#modeb(" + predicate + ")."


def generateNonBeBias(fluent):
    generalisedFluent = giveUniqueVariableNames(fluent)
    bias = set()
    time = "var(time)"
    happens = happensAt(generalisedFluent, time)
    bias.add(modeBWrapping(happens))
    return bias


def generateBeBias(fluent):
    generalisedFluent = giveUniqueVariableNames(fluent)
    bias = set()
    time = "var(time)"
    initiated = initiatedAt(generalisedFluent, time)
    holds = holdsAt(generalisedFluent, time)
    terminated = terminatedAt(generalisedFluent, time)
    bias.add(modeHWrapping(initiated))
    bias.add(modeBWrapping(holds))
    bias.add(modeHWrapping(terminated))
    return bias

def addTimePredicate(statement):
    time = set()
    time.add("time(" + str(statement.getLineID()) + ")")
    statement.setPredicates(time)

class BasicParser:
    def __init__(self, corpus):
        self.nlp = spacy.load("en_core_web_sm")
        self.synonymDictionary = {}
        self.previousQuestionIndex = -1
        self.conceptNet = ConceptNetIntegration()
        self.eventCalculusWrapper = EventCalculusWrapper()
        self.conceptsToExplore = set()
        self.corpus = corpus

    def parse(self, story, statement):
        if isinstance(statement, Question):
            # might be able to combine some of these steps
            self.parseQuestion(statement, story)

            # add in any new mode biases that have risen since the last question
            self.corpus.modeBias.update(self.generateModeBias(story, statement))
            index = story.getIndex(statement)
            if index + 1 == story.size():
                self.previousQuestionIndex = -1
            else:
                self.previousQuestionIndex = index
        else:
            self.parseStatement(statement)
        addTimePredicate(statement)


    # TODO can add predicates here dealing with the part of speech?
    def parseStatement(self, statement):
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
        fluent = formStatementFluent(fluent, root)
        fluent += ")"
        statement.setFluent(fluent)
        self.conceptsToExplore.update(conceptsToExplore)
        # do not need a return value now

    # TODO can add predicates here dealing with the part of speech?
    def parseQuestion(self, question: Question, story: Story):
        doc = self.nlp(question.getText())
        fluent = ""
        root = [token for token in doc if token.head == token][0]
        fluent += root.lemma_
        fluent += "("
        fluent = formQuestionFluent(fluent, root)
        fluent += ")"
        question.setFluent(fluent)
        self.synonymChecker(self.conceptsToExplore)
        self.updateFluents(story, question)
        self.setEventCalculusRepresentation(story, question)

    def updateFluents(self, story, statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            fluent = currentStatement.getFluent()
            if fluent:
                predicate = fluent.split('(')[0]
                if predicate in self.synonymDictionary.keys():
                    fluent = self.synonymDictionary[predicate] + '(' + fluent.split('(')[1]
                    currentStatement.setFluent(fluent)

    def setEventCalculusRepresentation(self, story, statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            fluent = currentStatement.getFluent()
            if fluent:
                self.eventCalculusWrapper.wrap(currentStatement)

    def generateModeBias(self, story: Story, statement):
        modeBias = set()
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            fluent = story.get(index).getFluent()
            if fluent:
                predicate = fluent.split('(')[0]
                if predicate == "be":
                    modeBias.update(generateBeBias(fluent))
                else:
                    modeBias.update(generateNonBeBias(fluent))
        return modeBias

    def checkCurrentSynonyms(self, concept):
        for value in self.synonymDictionary.values():
            if self.conceptNet.isSynonym(concept, value):
                self.synonymDictionary[concept] = value
                return True
        # tried adding because it might help
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
