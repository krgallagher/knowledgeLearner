from StoryStructure.Question import Question
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
        self.synonymDictionary.update(self.conceptNet.synonymFinder(self.conceptsToExplore))
        # to be removed at a later point
        if "drop" in self.synonymDictionary.keys():
            self.synonymDictionary["leave"] = self.synonymDictionary["drop"]
        self.updateFluents()
        self.setEventCalculusRepresentation()
        print(self.synonymDictionary)

    def setEventCalculusRepresentation(self):
        for story in self.trainCorpus:
            for sentence in story:
                wrap(sentence)
        for story in self.testCorpus:
            for sentence in story:
                wrap(sentence)