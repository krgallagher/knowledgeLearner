from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.DatasetPipeline import mainPipeline

if __name__ == '__main__':
    numberOfExamples = 100
    #for i in range(1, 21):
    i = 1
    train = "../en/qa" + str(i) + "_train.txt"
    test = "../en/qa" + str(i) + "_test.txt"
    trainingCorpus = bAbIReader(train)
    testingCorpus = bAbIReader(test)
    accuracy, parsingTime, learningTime = mainPipeline(trainingCorpus, testingCorpus, numberOfExamples, False)
    print("\nWithout Supervision:\n", "Accuracy: ", accuracy, "\nLearning Time: ", learningTime)
    trainingCorpus.reset()
    testingCorpus.reset()
    accuracy, parsingTime, learningTime = mainPipeline(trainingCorpus, testingCorpus, numberOfExamples, True)
    print("\nWith Supervision:\n", "Accuracy: ", accuracy, "\nLearning Time: ", learningTime)
