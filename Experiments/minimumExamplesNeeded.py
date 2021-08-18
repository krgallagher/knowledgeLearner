from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.DatasetPipeline import mainPipeline
import numpy as np

if __name__ == '__main__':
    trainingSet = "../en/qa" + "1" + "_train.txt"
    testingSet = "../en/qa" + "1" + "_test.txt"
    trainingCorpus = bAbIReader(trainingSet)
    testingCorpus = bAbIReader(testingSet)
    numShuffles = 5
    multiplier = 5
    numExamples = [5, 10, 25, 100]
    accuracies = np.empty([numShuffles, 5], dtype=float)
    for i in range(0, numShuffles):
        trainingCorpus.shuffle()
        for j in range(0, len(numExamples)):
            trainingCorpus.reset()
            testingCorpus.reset()
            accuracy, parsingTime, learningTime = mainPipeline(trainingCorpus, testingCorpus, numExamples[j])
            accuracies[i][j] = accuracy
            print("Shuffle ", i + 1, )
            print("Number of Examples: ", numExamples[j])
            print("Accuracy: ", accuracy)
    averageAccuracies = np.average(accuracies, axis=0)
    standardDeviations = np.std(accuracies, axis=0)
    for i in range(0, len(numExamples)):
        print("Number of Examples: ", numExamples[i])
        print("Average accuracy: ", averageAccuracies[i])
        print("Standard deviation: ", standardDeviations[i])
        print("----------------------------------------------------")
