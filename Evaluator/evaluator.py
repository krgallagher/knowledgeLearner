import random

from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.pipeline import mainPipeline

if __name__ == '__main__':
    trainingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa15_basic-deduction_train.txt"
    testingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa15_basic-deduction_test.txt"
    trainingReader = bAbIReader(trainingSet)
    testingReader = bAbIReader(testingSet)
    numShuffles = 5
    multiplier = 5
    for i in range(0, numShuffles):
        trainingReader.corpus.shuffle()
        print("Shuffle", i+1)
        for j in range(1, 6):
            #need to also reset the
            trainingReader.corpus.reset()
            testingReader.corpus.reset()
            accuracy = mainPipeline(trainingReader, testingReader, 5*j)
            print("Number of Examples: ", 5*j)
            print("Accuracy: ", accuracy)

#for each shuffle try with a different number of examples.
#multiple times for each
#look at Piotr's setup
