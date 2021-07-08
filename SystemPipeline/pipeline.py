from DatasetReader.bAbIReader import bAbIReader
from TranslationalModule.bAbIParser import bAbIParser

if __name__ == '__main__':

    # process data
    reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")

    # initialise parser
    parser = bAbIParser(reader.corpus)

    for story in reader.corpus:
        statements = story.getSentences()
        for statement in statements:
            parser.parse(statements, statement)



    #printing this out to see what happens
    for story in reader.corpus:
        statements = story.getSentences()
        for statement in statements:
            print(statement.getLineID(), statement.getText(), statement.getFluent(),
                  statement.getEventCalculusRepresentation(), statement.getPredicates())
    print(reader.corpus.modeBias)
