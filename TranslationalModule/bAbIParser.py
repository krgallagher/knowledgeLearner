from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from basicParser import Parser


class bAbIParser:
    def __init__(self, filename):
        self.reader = bAbIReader(filename)
        self.parser = Parser()
        self.fluents = []
        for story in self.reader.corpus:
            fluentsForStory = []
            statements = story.getSentences()
            for statement in statements:
                #need some notion of current concepts
                if isinstance(statement, Question):
                    fluent = self.parser.parseQuestion(statement)
                    #use the conceptNetIntegrationToEditTheFluents
                else:
                    fluent = self.parser.parseStatement(statement)
                    #could return list of relevant concepts which then we can merge as appropriate
                fluentsForStory.append((fluent, statement.getLineID()))
            print(fluentsForStory)
            self.fluents.append(fluentsForStory)

#will want to be able to do reasoning for each story
#


#here we can store the relevant fluents and timestamps for each story
#whenever a question occurs, then we need to go back to the beginning of the story and



def __str__(self):
    for fluent in self.fluents:
        print(fluent)


if __name__ == '__main__':
    parser = bAbIParser("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    for entry in parser.fluents:
        print(entry[1])
    #print(parser)
