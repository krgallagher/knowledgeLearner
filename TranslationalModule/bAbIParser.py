from StoryStructure.Question import Question
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import EventCalculusWrapper
from TranslationalModule.basicParser import BasicParser


class bAbIParser:
    def __init__(self, corpus):
        self.corpus = corpus
        self.parser = BasicParser()
        self.conceptNet = ConceptNetIntegration()
        self.synonymDictionary = {}
        self.eventCalculusWrapper = EventCalculusWrapper()
        self.conceptsToExplore = []
        self.previousQuestion = None

    def parse(self, statements, statement):
        if isinstance(statement, Question):
            fluent, concepts = self.parser.parseQuestion(statement)
            # self.conceptsToExplore += concepts
            # #will need to change this to be more general, but for now only want to deal with "be" verbs
            statement.setFluent(fluent)
            self.synonymChecker(self.conceptsToExplore)
            self.updateFluents(statements, statement)
            self.setEventCalculusRepresentation(statements, statement)
            # add in any new mode biases that have risen since the last question
            self.corpus.modeBias.update(self.parser.generateModeBias(statements, statement, self.previousQuestion))
            self.previousQuestion = statement
        else:
            fluent, concepts = self.parser.parseStatement(statement)
            self.conceptsToExplore += concepts
            statement.setFluent(fluent)

    def checkCurrentSynonyms(self, concept):
        for value in self.synonymDictionary.values():
            if self.conceptNet.isSynonym(concept, value):
                self.synonymDictionary[concept] = value
                return True
        return False

    def synonymChecker(self, concepts):
        conceptsCopy = concepts.copy()
        for concept in conceptsCopy:
            if concept in self.synonymDictionary.keys():
                concepts.remove(concept)
            elif self.checkCurrentSynonyms(concept):
                concepts.remove(concept)
        learnedConcepts = self.conceptNet.synonymFinder(concepts)
        self.synonymDictionary.update(learnedConcepts)

    # might want to update this with the getRange function
    def updateFluents(self, statements, statement):
        previousQuestionIndex, statementIndex = self.getRange(statement, statements)
        for index in range(previousQuestionIndex, statementIndex):
            currentStatement = statements[index]
            fluent = currentStatement.getFluent()
            if fluent:
                predicate = fluent.split('(')[0]
                if predicate in self.synonymDictionary.keys():
                    fluent = self.synonymDictionary[predicate] + '(' + fluent.split('(')[1]
                    currentStatement.setFluent(fluent)

    def setEventCalculusRepresentation(self, statements, statement):
        previousQuestionIndex, statementIndex = self.getRange(statement, statements)
        for index in range(previousQuestionIndex, statementIndex):
            currentStatement = statements[index]
            fluent = currentStatement.getFluent()
            if fluent:
                self.eventCalculusWrapper.wrap(currentStatement)

    def getRange(self, statement, statements):
        statementIndex = statements.index(statement) + 1
        previousQuestionIndex = 0
        if self.previousQuestion:
            if self.previousQuestion in statements:
                previousQuestionIndex = statements.index(self.previousQuestion)
        return previousQuestionIndex, statementIndex
