from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.BasicParser import BasicParser
from TranslationalModule.EventCalculus import wrap


class DatasetParser(BasicParser):
    def __init__(self, trainCorpus, testCorpus):
        super().__init__()
        self.trainCorpus = trainCorpus
        self.testCorpus = testCorpus

        # Set the doc for the training and testing corpus
        for story in self.trainCorpus:
            for sentence in story:
                sentence.doc = self.nlp(self.coreferenceFinder2(sentence, story))
        for story in self.testCorpus:
            for sentence in story:
                sentence.doc = self.nlp(self.coreferenceFinder2(sentence, story))

        # parse the training set questions
        for story in self.trainCorpus:
            for sentence in story:
                if isinstance(sentence, Question):
                    self.parse(sentence)
        # parse the testing set questions
        for story in self.testCorpus:
            for sentence in story:
                if isinstance(sentence, Question):
                    self.parse(sentence)
        for story in self.trainCorpus:
            for sentence in story:
                if not isinstance(sentence, Question):
                    self.parse(sentence)
            # parse the testing set questions
        for story in self.testCorpus:
            for sentence in story:
                if not isinstance(sentence, Question):
                    self.parse(sentence)

        # play around with the synonym dictionary
        self.synonymDictionary.update(self.conceptNet.synonymFinder(self.conceptsToExplore))
        # to be removed at a later point
        if "drop" in self.synonymDictionary.keys():
            self.synonymDictionary["leave"] = self.synonymDictionary["drop"]
        self.updateFluents()
        self.setEventCalculusRepresentation()
        print(self.synonymDictionary)

    def coreferenceFinder2(self, statement: Statement, story: Story):
        pronoun, possibilities = super().coreferenceFinder2(statement, story)
        #print(pronoun, possibilities)
        if not pronoun or not possibilities:
            return statement.text
        statementText = statement.text
        return statementText.replace(" " + pronoun + " ", " " + possibilities[0] + " ")


    def setEventCalculusRepresentation(self):
        for story in self.trainCorpus:
            for sentence in story:
                wrap(sentence)
        for story in self.testCorpus:
            for sentence in story:
                wrap(sentence)

if __name__ == '__main__':
    # process data
    # reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    trainCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task13_train")
    testCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task13_train")

    # initialise parser
    parser = DatasetParser(trainCorpus1, testCorpus1)

    for story1 in trainCorpus1:
        for sentence1 in story1:
            print(sentence1.getText(), sentence1.getLineID(), sentence1.getFluents(),
                  sentence1.getEventCalculusRepresentation(), sentence1.getPredicates(), sentence1.getModeBiasFluents())
            if isinstance(sentence1, Question):
                print(sentence1.getModeBiasFluents())
    print(trainCorpus1.modeBias)
    print(parser.synonymDictionary)
