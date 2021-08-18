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
                self.setDocAndExtractProperNouns(sentence, story)
        for story in self.testCorpus:
            for sentence in story:
                self.setDocAndExtractProperNouns(sentence, story)

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

        self.synonymDictionary.update(self.conceptNet.synonymFinder(self.conceptsToExplore))
        self.updateFluents()
        self.setEventCalculusRepresentation()
        self.assembleModeBias()

    def setDocAndExtractProperNouns(self, sentence, story):
        sentence.doc = self.nlp(self.coreferenceFinder(sentence, story))
        self.properNouns.update(self.getProperNouns(sentence))

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

    def assembleModeBias(self):
        if self.useSupervision:
            for story in self.trainCorpus:
                for sentence in story:
                    if isinstance(sentence, Question):
                        for hint in sentence.getHints():
                            self.addModeBias(story.get(int(hint) - 1))
                        self.addModeBias(sentence)
        else:
            for story in self.trainCorpus:
                for sentence in story:
                    self.addModeBias(sentence)

            for story in self.testCorpus:
                for sentence in story:
                    self.addModeBias(sentence)

    def addModeBias(self, sentence):
        nonECModeBias, ECModeBias = self.addStatementModeBias(sentence)
        self.trainCorpus.updateECModeBias(ECModeBias)
        self.trainCorpus.updateNonECModeBias(nonECModeBias)
        self.trainCorpus.updateConstantModeBias(sentence.getConstantModeBias())


if __name__ == '__main__':
    trainCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task20_train")
    testCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task20_train")

    parser = DatasetParser(trainCorpus1, testCorpus1)

    for story1 in trainCorpus1:
        for sentence1 in story1:
            print(sentence1.getText(), sentence1.getLineID(), sentence1.getFluents(),
                  sentence1.getEventCalculusRepresentation(), sentence1.getPredicates(), sentence1.getModeBiasFluents(),
                  sentence1.constantModeBias)
            if isinstance(sentence1, Question):
                print(sentence1.getModeBiasFluents(), sentence1.getAnswer())
    print(trainCorpus1.ECModeBias)
    print(parser.synonymDictionary)
    for story1 in testCorpus1:
        for sentence1 in story1:
            print(sentence1.getText(), sentence1.getLineID(), sentence1.getFluents(),
                  sentence1.getEventCalculusRepresentation(), sentence1.getPredicates(),
                  sentence1.getModeBiasFluents(),
                  sentence1.constantModeBias)
            if isinstance(sentence1, Question):
                print(sentence1.getModeBiasFluents(), sentence1.getAnswer())
    print(trainCorpus1.ECModeBias)
    print(trainCorpus1.nonECModeBias)
    print(trainCorpus1.constantModeBias)
    print(parser.synonymDictionary)
