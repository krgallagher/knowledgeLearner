from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.DatasetPipeline import DatasetPipeline

if __name__ == '__main__':
    tasks = [1, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20]
    for task in tasks:
        print("Task: ", task)
        trainingSet = "../en/qa" + str(task) + "_train.txt"
        testingSet = "../en/qa" + str(task) + "_test.txt"
        trainingCorpus = bAbIReader(trainingSet)
        testingCorpus = bAbIReader(testingSet)
        accuracy, parsingTime, learningTime = DatasetPipeline(trainingCorpus, testingCorpus)
        print("Accuracy: ", accuracy)
        print("Parsing time: ", parsingTime)
        print("Learning time: ", learningTime)
        print("----------------------------------------------------")
