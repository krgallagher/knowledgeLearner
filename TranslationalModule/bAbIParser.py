from StoryStructure.Question import Question
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculusWrapper import EventCalculusWrapper
from TranslationalModule.basicParser import BasicParser

#add a function here to generate the mode bias

#in the code below I'm implicitly making the assumption that all stories have and end with a question
#that is fine because you don't need to generate mode bias if you aren't going to ask any questions?
#could fix this/other issues by adding a clause saying if it is the end of a story and the last Question is way before
#then run those tasks to gather synonyms, etc.

#might want to migrate some of the built in functions to the basicParser so that they may be used in greater generality

class bAbIParser:
    def __init__(self, corpus):
        self.corpus = corpus
        self.parser = BasicParser()
        self.conceptNet = ConceptNetIntegration()
        self.synonymDictionary = {}
        self.eventCalculusWrapper = EventCalculusWrapper()
        for story in self.corpus:
            statements = story.getSentences()
            conceptsToExplore = []
            previousQuestion = None
            for statement in statements:
                if isinstance(statement, Question):
                    fluent, concepts = self.parser.parseQuestion(statement)
                    self.synonymChecker(conceptsToExplore)
                    self.updateFluents(statements, statement, previousQuestion)
                    self.setEventCalculusRepresentation(statements, statement, previousQuestion)
                    # add in any new mode biases that have risen since the last question
                    self.corpus.update(self.parser.generateModeBias(statements, statement, previousQuestion))
                    previousQuestion = statement
                else:
                    fluent, concepts = self.parser.parseStatement(statement)
                    conceptsToExplore += concepts
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


    def updateFluents(self, statements, statement, previousQuestion):
        statementIndex = statements.index(statement)
        previousQuestionIndex = 0
        if previousQuestion:
            previousQuestionIndex = statements.index(previousQuestion)
        for index in range(previousQuestionIndex, statementIndex):
            currentStatement = statements[index]
            fluent = currentStatement.getFluent()
            if fluent:
                predicate = fluent.split('(')[0]
                if predicate in self.synonymDictionary.keys():
                    fluent = self.synonymDictionary[predicate] + '(' + fluent.split('(')[1]
                    currentStatement.setFluent(fluent)

    def setEventCalculusRepresentation(self, statements, statement, previousQuestion):
        statementIndex = statements.index(statement)
        previousQuestionIndex = 0
        if previousQuestion:
            previousQuestionIndex = statements.index(previousQuestion)
        for index in range(previousQuestionIndex, statementIndex):
            currentStatement = statements[index]
            fluent = currentStatement.getFluent()
            if fluent:
                self.eventCalculusWrapper.wrap(currentStatement)




"""
if __name__ == '__main__':
    parser = bAbIParser("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")
    for story in parser.corpus:
        statements = story.getSentences()
        for statement in statements:
            print(statement.getLineID(), statement.getText(), statement.getLogicalRepresentation())
"""
