from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.DatasetPipeline import DatasetPipeline
import numpy as np

if __name__ == '__main__':
    numberOfExamples = 200
    numShuffles = 5
    tasks = [1, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20]
    for task in tasks:
        print("Task", task)
        train = "../en/qa" + str(task) + "_train.txt"
        test = "../en/qa" + str(task) + "_test.txt"
        trainingCorpus = bAbIReader(train)
        testingCorpus = bAbIReader(test)

        accuracies = np.empty([numShuffles, 2], dtype=float)
        parsingTimes = np.empty([numShuffles, 2], dtype=float)
        learningTimes = np.empty([numShuffles, 2], dtype=float)
        for i in range(0, numShuffles):
            trainingCorpus.reset()
            testingCorpus.reset()
            trainingCorpus.shuffle()
            accuracies[i][0], parsingTimes[i][0], learningTimes[i][0] = DatasetPipeline(trainingCorpus, testingCorpus,
                                                                                        numberOfExamples, False)

            trainingCorpus.reset()
            testingCorpus.reset()
            accuracies[i][1], parsingTimes[i][1], learningTimes[i][1] = DatasetPipeline(trainingCorpus, testingCorpus,
                                                                                        numberOfExamples, True)

        averageAccuracies = np.average(accuracies, axis=0)
        accuraciesStandardDeviations = np.std(accuracies, axis=0)

        averageLearningTimes = np.average(learningTimes, axis=0)
        learningTimesStandardDeviations = np.std(learningTimes, axis=0)

        averageParsingTimes = np.average(parsingTimes, axis=0)
        parsingTimesStandardDeviation = np.std(parsingTimes, axis=0)

        print("Without Supervision: ")
        print("Average accuracy: ", averageAccuracies[0])
        print("Standard deviation: ", accuraciesStandardDeviations[0])
        print("Average learning time: ", averageLearningTimes[0])
        print("Standard deviation: ", learningTimesStandardDeviations[0])
        print("Average parsing time: ", averageParsingTimes[0])
        print("Standard deviation: ", parsingTimesStandardDeviation[0])
        print("----------------------------------------------------\n")
        print("With Supervision: ")
        print("Average accuracy: ", averageAccuracies[1])
        print("Standard deviation: ", accuraciesStandardDeviations[1])
        print("Average learning time: ", averageLearningTimes[1])
        print("Standard deviation: ", learningTimesStandardDeviations[1])
        print("Average parsing time: ", averageParsingTimes[1])
        print("Standard deviation: ", parsingTimesStandardDeviation[1])
        print("----------------------------------------------------\n")
