from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.BasicParser import BasicParser, getSubstitutedText
from TranslationalModule.EventCalculus import wrap


class DatasetParser(BasicParser):
    def __init__(self, trainCorpus, testCorpus):
        super().__init__()
        self.trainCorpus = trainCorpus
        self.testCorpus = testCorpus

        # Set the doc for the training and testing corpus
        for story in self.trainCorpus:
            for sentence in story:
                sentence.doc = self.nlp(self.coreferenceFinder(sentence, story))
        for story in self.testCorpus:
            for sentence in story:
                sentence.doc = self.nlp(self.coreferenceFinder(sentence, story))

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
        # self.synonymDictionary.update(self.conceptNet.synonymFinder(self.conceptsToExplore))
        # to be removed at a later point
        # if "drop" in self.synonymDictionary.keys():
        #    self.synonymDictionary["leave"] = self.synonymDictionary["drop"]
        self.synonymDictionary = {'put_down': 'drop', 'go_to': 'go_to', 'journey_to': 'go_to', 'get': 'take',
                                  'move_to': 'go_to', 'grab': 'take', "go": "go_to",
                                  'take': 'take', 'travel_to': 'go_to', 'drop': 'drop', 'leave': 'drop',
                                  'pick_up': 'take', 'discard': 'drop', "go_after": "go_to", "hand_to": "give_to",
                                  "give_to": "give_to", "pass_to": "give_to"}

        self.updateFluents()
        self.setEventCalculusRepresentation()
        print(self.synonymDictionary)

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
                fluents, modeBiasFluents = sentence.getFluents(), sentence.getModeBiasFluents()
                sentence.setFluents(self.update(fluents))
                sentence.setModeBiasFluents(self.update(modeBiasFluents))
        for story in self.testCorpus:
            for sentence in story:
                fluents, modeBiasFluents = sentence.getFluents(), sentence.getModeBiasFluents()
                sentence.setFluents(self.update(fluents))
                sentence.setModeBiasFluents(self.update(modeBiasFluents))


if __name__ == '__main__':
    trainCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task18_train")
    testCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task18_test")

    parser = DatasetParser(trainCorpus1, testCorpus1)

    for story1 in trainCorpus1:
        for sentence1 in story1:
            print(sentence1.getText(), sentence1.getLineID(), sentence1.getFluents(),
                  sentence1.getEventCalculusRepresentation(), sentence1.getPredicates(), sentence1.getModeBiasFluents(),
                  sentence1.constantModeBias)
            if isinstance(sentence1, Question):
                print(sentence1.getModeBiasFluents(), sentence1.getAnswer())
    print(trainCorpus1.modeBias)
    print(parser.synonymDictionary)
    for story1 in testCorpus1:
        for sentence1 in story1:
            print(sentence1.getText(), sentence1.getLineID(), sentence1.getFluents(),
                  sentence1.getEventCalculusRepresentation(), sentence1.getPredicates(),
                  sentence1.getModeBiasFluents(),
                  sentence1.constantModeBias)
            if isinstance(sentence1, Question):
                print(sentence1.getModeBiasFluents(), sentence1.getAnswer())
    print(trainCorpus1.modeBias)
    print(parser.synonymDictionary)
