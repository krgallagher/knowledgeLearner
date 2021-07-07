from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from basicParser import Parser


class bAbIParser:
    def __init__(self, filename):
        self.reader = bAbIReader(filename)
        self.parser = Parser()
        self.conceptNet = ConceptNetIntegration()
        self.synonymDictionary = {}
        for story in self.reader.corpus:
            statements = story.getSentences()
            conceptsToExplore = []
            for statement in statements:
                if isinstance(statement, Question):
                    fluent, concepts = self.parser.parseQuestion(statement)
                    self.synonymChecker(conceptsToExplore)
                    self.updateFluents(statements, statement)

                    # maybe we should not clear the concepts and only delete the ones we have linked up
                    # might be difficult to edit the fluent later on
                    # conceptsToExplore.clear()
                else:
                    fluent, concepts = self.parser.parseStatement(statement)
                    conceptsToExplore += concepts
                statement.setLogicalRepresentation(fluent)

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


    def updateFluents(self, statements, statement):
        statementIndex = statements.index(statement)
        for currentStatement in statements:
            fluent = currentStatement.getLogicalRepresentation()
            if fluent:
                predicate = fluent.split('(')[0]
                if predicate in self.synonymDictionary.keys():
                    fluent = self.synonymDictionary[predicate] + '(' + fluent.split('(')[1]
                    currentStatement.setLogicalRepresentation(fluent)
            if statements.index(currentStatement) == statementIndex:
                return


def __str__(self):
    for fluent in self.fluents:
        print(fluent)


if __name__ == '__main__':
    parser = bAbIParser("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")
    for story in parser.reader.corpus:
        statements = story.getSentences()
        for statement in statements:
            print(statement.getLineID(), statement.getText(), statement.getLogicalRepresentation())

