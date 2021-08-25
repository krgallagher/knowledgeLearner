from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.BasicParser import BasicParser, getSubstitutedText
from TranslationalModule.EventCalculus import wrap


class DatasetParser(BasicParser):
    def __init__(self, trainCorpus, testCorpus, useSupervision=False):
        super().__init__()
        self.trainCorpus = trainCorpus
        self.testCorpus = testCorpus
        self.useSupervision = useSupervision

        for story in self.trainCorpus:
            for sentence in story:
                sentence.doc = self.nlp(self.coreferenceFinder(sentence, story))
        for story in self.testCorpus:
            for sentence in story:
                sentence.doc = self.nlp(self.coreferenceFinder(sentence, story))

        for story in self.trainCorpus:
            for sentence in story:
                if isinstance(sentence, Question):
                    self.parse(sentence)

        for story in self.testCorpus:
            for sentence in story:
                if isinstance(sentence, Question):
                    self.parse(sentence)

        for story in self.trainCorpus:
            for sentence in story:
                if not isinstance(sentence, Question):
                    self.parse(sentence)

        for story in self.testCorpus:
            for sentence in story:
                if not isinstance(sentence, Question):
                    self.parse(sentence)

        self.synonymDictionary.update(self.conceptNet.similarPredicateFinder(self.conceptsToExplore))
        self.updateFluents()
        self.setEventCalculusRepresentation()


    def coreferenceFinder(self, statement: Statement, story: Story):
        pronoun, possibilities = super().coreferenceFinder(statement, story)
        if not pronoun or not possibilities:
            return statement.text
        return getSubstitutedText(pronoun, possibilities[0], statement)

    def setEventCalculusRepresentation(self):
        for story in self.trainCorpus:
            for sentence in story:
                wrap(sentence)
        for story in self.testCorpus:
            for sentence in story:
                wrap(sentence)

    def updateFluents(self):
        for story in self.trainCorpus:
            for sentence in story:
                self.updateSentence(sentence)
        for story in self.testCorpus:
            for sentence in story:
                self.updateSentence(sentence)




if __name__ == '__main__':
    trainingSet = "../en/qa" + "8" + "_train.txt"
    testingSet = "../en/qa" + "8" + "_test.txt"

    trainCorpus1 = bAbIReader(trainingSet)
    testCorpus1 = bAbIReader(testingSet)

    parser = DatasetParser(trainCorpus1, testCorpus1)

    '''
    for story1 in trainCorpus1:
        for sentence1 in story1:
            print(sentence1.getText(), sentence1.getLineID(), sentence1.getFluents(),
                  sentence1.getEventCalculusRepresentation(), sentence1.getModeBiasFluents(),
                  sentence1.constantModeBias)
            if isinstance(sentence1, Question):
                print(sentence1.getModeBiasFluents(), sentence1.getAnswer())
    for story1 in testCorpus1:
        for sentence1 in story1:
            print(sentence1.getText(), sentence1.getLineID(), sentence1.getFluents(),
                  sentence1.getEventCalculusRepresentation(),
                  sentence1.getModeBiasFluents(),
                  sentence1.constantModeBias)
            if isinstance(sentence1, Question):
                print(sentence1.getModeBiasFluents(), sentence1.getAnswer())
    '''