import spacy
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Story
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import holdsAt, happensAt, initiatedAt, terminatedAt, wrap


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


def generateBeBias(modeBiasFluent, statement: Statement):
    bias = set()
    time = varWrapping("time")
    initiated = initiatedAt(modeBiasFluent, time)
    holds = holdsAt(modeBiasFluent, time)
    terminated = terminatedAt(modeBiasFluent, time)
    bias.add(modeHWrapping(initiated))
    bias.add(modeBWrapping(holds))
    bias.add(modeHWrapping(terminated))
    if not isinstance(statement, Question):
        bias.add(modeBWrapping(initiated))
    return bias


def timePredicate(statement: Statement):
    time = "time(" + str(statement.getLineID()) + ")"
    return time


def formStatementFluent(statement: Statement, fluent, modeBiasFluent, doc):
    nouns = [token for token in doc if "NN" in token.tag_]
    for noun in nouns:
        tag = noun.tag_.lower()
        lemma = noun.lemma_.lower()
        if fluent[-1] != '(':
            fluent += ','
            modeBiasFluent += ','
        fluent += lemma
        modeBiasFluent += varWrapping(tag)
        # add tag predicates
        relevantPredicate = tag + '(' + lemma + ')'
        statement.addPredicate(relevantPredicate)
    return fluent, modeBiasFluent


def formQuestionFluent(question: Question, fluent, modeBiasFluent, doc):
    fluent, modeBiasFluent = formStatementFluent(question, fluent, modeBiasFluent, doc)
    if "where" or "what" in question.getText():
        if not fluent[-1] == '(':
            fluent += ','
            modeBiasFluent += ','
        fluent += "V1"
        modeBiasFluent += varWrapping('nn')

    return fluent, modeBiasFluent


class BasicParser:
    def __init__(self, corpus):
        self.nlp = spacy.load("en_core_web_lg")
        self.synonymDictionary = {}
        self.previousQuestionIndex = -1
        self.conceptNet = ConceptNetIntegration()
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
        negation = [token for token in doc if token.dep_ == 'neg' and token.tag_ == 'RB']
        verb_modifier = [token for token in doc if token.dep_ == 'acomp']
        if negation:
            statement.negatedVerb = True
        fluent += root.lemma_
        if adposition and fluent != 'be':
            fluent += '_' + adposition[0].text
        if verb_modifier:
            fluent += '_' + verb_modifier[0].lemma_
        conceptsToExplore = set()
        if fluent != 'be':
            conceptsToExplore.add(fluent)
        fluent += "("
        modeBiasFluent = fluent
        fluent, modeBiasFluent = formStatementFluent(statement, fluent, modeBiasFluent, doc)
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
        verb_modifier = [token for token in doc if token.dep_ == 'acomp']
        if verb_modifier:
            fluent += '_' + verb_modifier[0].lemma_
        fluent += "("
        modeBiasFluent = fluent
        fluent, modeBiasFluent = formQuestionFluent(question, fluent, modeBiasFluent, doc)
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


    #to do tidy this up and even tidy up the name of this
    def setEventCalculusRepresentation(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            fluent = currentStatement.getFluent()
            modeBiasFluent = currentStatement.getModeBiasFluent()
            wrap(currentStatement)
            predicate = fluent.split('(')[0]
            if predicate == "be":
                modeBias = generateBeBias(modeBiasFluent, currentStatement)
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
    reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task15_train")

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
