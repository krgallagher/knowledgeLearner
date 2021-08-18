from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.DatasetPipeline import mainPipeline
import numpy as np

if __name__ == '__main__':
    numberOfExamples = 100
    numShuffles = 5
    i = 1
    train = "../en/qa" + str(i) + "_train.txt"
    test = "../en/qa" + str(i) + "_test.txt"
    trainingCorpus = bAbIReader(train)
    testingCorpus = bAbIReader(test)

    accuracies = np.empty([numShuffles, 2], dtype=float)
    parsingTimes = np.empty([numShuffles, 2], dtype=float)
    learningTimes = np.empty([numShuffles, 2], dtype=float)

    for i in range(0, numShuffles):
        trainingCorpus.reset()
        testingCorpus.reset()
        trainingCorpus.shuffle()
        accuracy, parsingTime, learningTime = mainPipeline(trainingCorpus, testingCorpus, numberOfExamples, False)
        accuracies[i][0] = accuracy
        parsingTimes[i][0] = parsingTime
        learningTimes[i][0] = learningTimes
        print("\nWithout Supervision:\n", "Accuracy: ", accuracy, "\nLearning Time: ", learningTime)

        trainingCorpus.reset()
        testingCorpus.reset()
        accuracy, parsingTime, learningTime = mainPipeline(trainingCorpus, testingCorpus, numberOfExamples, True)
        accuracies[i][1] = accuracy
        parsingTimes[i][1] = parsingTime
        learningTimes[i][1] = learningTimes
        print("\nWith Supervision:\n", "Accuracy: ", accuracy, "\nLearning Time: ", learningTime)

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
