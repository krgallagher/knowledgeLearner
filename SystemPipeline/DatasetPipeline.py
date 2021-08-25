import time
from DatasetReader.bAbIReader import bAbIReader
from LearningModule.learner import Learner
from LearningModule.modeBiasGenerator import ModeBiasGenerator
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Corpus import pruneCorpus
from StoryStructure.Question import Question
from TranslationalModule.ChoiceRulesChecker import choiceRulesPresent
from TranslationalModule.DatasetParser import DatasetParser
from TranslationalModule.ExpressivityChecker import isEventCalculusNeeded

MAX_EXAMPLES = 1000


def mainPipeline(trainCorpus, testCorpus, numExamples=MAX_EXAMPLES, useSupervision=False,
                 useExpressivityChecker=(True, None)):
    startTime = time.time()

    if numExamples < MAX_EXAMPLES:
        trainCorpus = pruneCorpus(trainCorpus, numExamples)

    DatasetParser(trainCorpus, testCorpus, useSupervision=useSupervision)
    parseEndTime = time.time()

    reasoner = Reasoner(trainCorpus)

    learner = Learner(trainCorpus, useSupervision=useSupervision)

    if useExpressivityChecker[0]:
        trainCorpus.isEventCalculusNeeded = isEventCalculusNeeded(trainCorpus)
    else:
        trainCorpus.isEventCalculusNeeded = useExpressivityChecker[1]

    trainCorpus.choiceRulesPresent = choiceRulesPresent(trainCorpus)

    train(trainCorpus, reasoner, learner, useSupervision)
    learningTime = time.time()

    numQuestions = 0
    numCorrect = 0

    for story in testCorpus:
        for sentence in story:
            if isinstance(sentence, Question):
                numQuestions += 1
                answerToQuestion = reasoner.computeAnswer(sentence, story)
                if sentence.isCorrectAnswer(answerToQuestion):
                    numCorrect += 1
                # print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
                #      sentence.getAnswer(), answerToQuestion, sentence.getHints())
    print("Hypotheses: ", trainCorpus.getHypotheses())
    # print("Parsing Time: ", parseEndTime - startTime)
    # print("Learning Time: ", learningTime - parseEndTime)
    # print("Accuracy: ", numCorrect/numQuestions)
    return numCorrect / numQuestions, parseEndTime - startTime, learningTime - parseEndTime


def train(corpus, reasoner, learner, useSupervision):
    modeBiasGenerator = ModeBiasGenerator(corpus, useSupervision)
    modeBiasGenerator.assembleModeBias()
    for story in corpus:
        for sentence in story:
            if isinstance(sentence, Question):
                answerToQuestion = reasoner.computeAnswer(sentence, story)
                # print(sentence.text, sentence.answer, answerToQuestion)
                if not sentence.isCorrectAnswer(answerToQuestion):
                    learner.learn(sentence, story, answerToQuestion)


if __name__ == '__main__':
    trainingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task20_train"
    testingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task20_test"
    # trainingSet = "../en/qa" + "15" + "_train.txt"
    # testingSet = "../en/qa" + "15" + "_test.txt"
    trainingCorpus = bAbIReader(trainingSet)
    testingCorpus = bAbIReader(testingSet)
    mainPipeline(trainingCorpus, testingCorpus, useSupervision=False, useExpressivityChecker=(False, True))
