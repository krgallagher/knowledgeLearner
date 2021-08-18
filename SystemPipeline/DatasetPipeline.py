import time
from DatasetReader.bAbIReader import bAbIReader
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Corpus import pruneCorpus
from StoryStructure.Question import Question
from TranslationalModule.ChoiceRulesChecker import choiceRulesPresent
from TranslationalModule.DatasetParser import DatasetParser
from TranslationalModule.ExpressivityChecker import isEventCalculusNeeded

MAX_EXAMPLES = 1000


def mainPipeline(trainCorpus, testCorpus, numExamples=MAX_EXAMPLES, useSupervision=False):
    startTime = time.time()

    if numExamples < MAX_EXAMPLES:
        trainCorpus = pruneCorpus(trainCorpus, numExamples)

    DatasetParser(trainCorpus, testCorpus, useSupervision=useSupervision)
    parseEndTime = time.time()

    reasoner = Reasoner(trainCorpus)

    learner = Learner(trainCorpus, useSupervision=useSupervision)

    if isEventCalculusNeeded(trainCorpus):
        trainCorpus.isEventCalculusNeeded = True

    if choiceRulesPresent(trainCorpus):
        trainCorpus.choiceRulesPresent = True

    train(trainCorpus, reasoner, learner)
    learningTime = time.time()

    hypotheses = trainCorpus.getHypotheses()

    testCorpus.setHypotheses(hypotheses)

    numQuestions = 0
    numCorrect = 0

    for story in testCorpus:
        for sentence in story:
            if isinstance(sentence, Question):
                numQuestions += 1
                answerToQuestion = reasoner.computeAnswer(sentence, story)
                if sentence.isCorrectAnswer(answerToQuestion):
                    numCorrect += 1
                # else:
                #    print(story)
                print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
                      sentence.getAnswer(), answerToQuestion, sentence.getHints())
    print("Number Correct: ", numCorrect)
    print("Number of Question: ", numQuestions)
    print("Accuracy: ", numCorrect / numQuestions)
    print("Hypotheses: ", trainCorpus.getHypotheses())
    print("Parsing Time: ", parseEndTime - startTime)
    print("Learning Time: ", learningTime - parseEndTime)
    return numCorrect / numQuestions, parseEndTime - startTime, learningTime - parseEndTime


def train(corpus, reasoner, learner):
    for story in corpus:
        for sentence in story:
            if isinstance(sentence, Question):
                answerToQuestion = reasoner.computeAnswer(sentence, story)
                print(sentence.text, sentence.answer, answerToQuestion)
                if not sentence.isCorrectAnswer(answerToQuestion):
                    learner.learn(sentence, story, answerToQuestion)


if __name__ == '__main__':
    trainingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task20_train"
    testingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task20_test"
    trainingCorpus = bAbIReader(trainingSet)
    testingCorpus = bAbIReader(testingSet)
    mainPipeline(trainingCorpus, testingCorpus, useSupervision=False)
