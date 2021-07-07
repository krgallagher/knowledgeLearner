from DatasetReader.bAbIReader import bAbIReader
from TranslationalModule.bAbIParser import bAbIParser

if __name__ == '__main__':
    reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")
    parser = bAbIParser(reader.corpus)
    for story in reader.corpus:
        statements = story.getSentences()
        for statement in statements:
            print(statement.getLineID(), statement.getText(), statement.getFluent(), statement.getEventCalculusRepresentation())

