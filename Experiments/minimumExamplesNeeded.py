from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.DatasetPipeline import DatasetPipeline
import numpy as np

if __name__ == '__main__':
    tasks = [1, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20]
    for task in tasks:
        print("Task: ", task)
        trainingSet = "../en/qa" + str(task) + "_train.txt"
        testingSet = "../en/qa" + str(task) + "_test.txt"
        trainingCorpus = bAbIReader(trainingSet)
        testingCorpus = bAbIReader(testingSet)
        numShuffles = 5
        numExamples = [5, 10, 25, 100, 200]
        accuracies = np.empty([numShuffles, len(numExamples)], dtype=float)
        for i in range(0, numShuffles):
            trainingCorpus.shuffle()
            for j in range(0, len(numExamples)):
                trainingCorpus.reset()
                testingCorpus.reset()
                accuracy, parsingTime, learningTime = DatasetPipeline(trainingCorpus, testingCorpus, numExamples[j])
                accuracies[i][j] = accuracy
        averageAccuracies = np.average(accuracies, axis=0)
        standardDeviations = np.std(accuracies, axis=0)
        for i in range(0, len(numExamples)):
            print("Number of Examples: ", numExamples[i])
            print("Average accuracy: ", averageAccuracies[i])
            print("Standard deviation: ", standardDeviations[i])
            print("----------------------------------------------------")
