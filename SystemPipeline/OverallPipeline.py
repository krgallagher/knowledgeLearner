import sys
from DatasetReader.bAbIReader import bAbIReader
from SystemPipeline.DatasetPipeline import DatasetPipeline
from SystemPipeline.InteractivePipeline import InteractivePipeline


def printUsageMenu():
    print("General Usage: -component=[dataset|dialogue] [requiredInformation] [options]")
    print("if -component=dataset is chosen: ")
    print("\t[requiredInformation] == [trainingFile, testingFile]")
    print("\t [options]: ")
    print("\t\t -s : Use strong supervision for training")
    print("\t\t -r=[EventCalculus|Fluent]: Use the specified representation for training and testing")
    print("if -component=dialogue is chosen: ")
    print("\t[requiredInformation] == [-dialogueMethod=[spoken|written]]")

def getAdditionalFlags(inputs):
    supervision = False
    expressivityChecker = (True, None)
    if '-s' in inputs:
        supervision = True
    if '-r=EventCalculus' in inputs:
        expressivityChecker = (False, True)
    if '-r=Fluent' in inputs:
        expressivityChecker = (False, False)
    return supervision, expressivityChecker


def getDialogueMethod(input):
    if input == '-dialogueMethod=spoken':
        return True
    elif input == '-dialogueMethod=written':
        return False
    return None


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == '-component=dataset':
        try:
            trainingFile = sys.argv[2]
            testingFile = sys.argv[3]
            useSupervision, useExpressivityChecker = getAdditionalFlags(sys.argv)
            trainingCorpus = bAbIReader(trainingFile)
            testingCorpus = bAbIReader(testingFile)
            accuracy, parsingTime, learningTime = DatasetPipeline(trainingCorpus, testingCorpus,
                                                                  useSupervision=useSupervision,
                                                                  useExpressivityChecker=useExpressivityChecker)
            print("Parsing Time:", parsingTime, ",Learning Time: ", learningTime, ",Accuracy: ", accuracy)
        except FileNotFoundError:
            printUsageMenu()
    elif len(sys.argv) >= 3 and sys.argv[1] == '-component=dialogue':
        dialogueMethod = getDialogueMethod(sys.argv[2])
        if dialogueMethod is not None:
            system = InteractivePipeline(audio=dialogueMethod)
        else:
            printUsageMenu()
    else:
        printUsageMenu()

