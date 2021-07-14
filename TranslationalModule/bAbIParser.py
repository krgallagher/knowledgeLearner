from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from TranslationalModule.basicParser import BasicParser

# might want to remake this a part of the class


class bAbIParser(BasicParser):
    def __init__(self, corpus):
        super().__init__()
        self.corpus = corpus



if __name__ == '__main__':
    # process data
    #reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task2_train")

    # get corpus
    corpus = reader.corpus

    # initialise parser
    parser = bAbIParser(corpus)

    for story in reader.corpus:
        for sentence in story:
            parser.parse(story, sentence)
        for sentence in story:
            print(sentence.getText(), sentence.getLineID(), sentence.getFluent(), sentence.getEventCalculusRepresentation())
        print(parser.synonymDictionary)