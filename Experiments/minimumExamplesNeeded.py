import random

from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.pipeline import mainPipeline

if __name__ == '__main__':
    trainingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa15_basic-deduction_train.txt"
    testingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa15_basic-deduction_test.txt"
    trainingCorpus = bAbIReader(trainingSet)
    testingCorpus = bAbIReader(testingSet)
    numShuffles = 5
    multiplier = 5
    for i in range(0, numShuffles):
        trainingCorpus.trainCorpus.shuffle()
        print("Shuffle", i + 1)
        for j in range(1, 6):
            trainingCorpus.reset()
            testingCorpus.reset()
            accuracy = mainPipeline(trainingCorpus, testingCorpus, 5 * j)
            print("Number of Examples: ", 5 * j)
            print("Accuracy: ", accuracy)


# with/without concept net, learning time
# leave vocabulary unlearned with less examples
#parser still add to the test set.
#parse the test set once.