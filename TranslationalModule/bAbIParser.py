from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import EventCalculusWrapper
from TranslationalModule.basicParser import BasicParser


def addTimePredicate(statement):
    time = set()
    time.add("time(" + str(statement.getLineID()) + ")")
    statement.setPredicates(time)


class bAbIParser:
    def __init__(self, corpus):
        self.corpus = corpus
        self.parser = BasicParser()
        self.conceptNet = ConceptNetIntegration()
        self.synonymDictionary = {}
        self.eventCalculusWrapper = EventCalculusWrapper()
        self.conceptsToExplore = []
        self.previousQuestionIndex = -1

    def parse(self, story, statement):
        if isinstance(statement, Question):
            fluent, concepts = self.parser.parseQuestion(statement)
            statement.setFluent(fluent)
            self.synonymChecker(self.conceptsToExplore)
            self.updateFluents(story, statement)
            self.setEventCalculusRepresentation(story, statement)
            # add in any new mode biases that have risen since the last question
            self.corpus.modeBias.update(self.parser.generateModeBias(story, statement, self.previousQuestionIndex))
            index = story.getIndex(statement)
            if index == 14:
                self.previousQuestionIndex = -1
            else:
                self.previousQuestionIndex = index
        else:
            fluent, concepts = self.parser.parseStatement(statement)
            self.conceptsToExplore += concepts
            statement.setFluent(fluent)
        addTimePredicate(statement)

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




if __name__ == '__main__':
    # process data
    reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    # reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")

    # get corpus
    corpus = reader.corpus

    # initialise parser
    parser = bAbIParser(corpus)

    for story in reader.corpus:
        for sentence in story:
            parser.parse(story, sentence)
        for sentence in story:
            if sentence.getEventCalculusRepresentation() is None:
                print(sentence.getText(), sentence.getLineID(), sentence.getFluent())
