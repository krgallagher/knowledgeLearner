import time
from DatasetReader.bAbIReader import bAbIReader
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Corpus import pruneCorpus
from StoryStructure.Question import Question
from TranslationalModule.ChoiceRulesChecker import choiceRulesPresent
from TranslationalModule.DatasetParser import DatasetParser
from TranslationalModule.ExpressivityChecker import isEventCalculusNeeded


def mainPipeline(trainCorpus, testCorpus, numExamples=10000, useSupervision=False):
    startTime = time.time()

    if numExamples < 10000:  # alternatively could do 1000
        trainCorpus = pruneCorpus(trainCorpus, numExamples)

    # initialise parser
    DatasetParser(trainCorpus, testCorpus)
    parseEndTime = time.time()

    # initialise reasoner
    reasoner = Reasoner(trainCorpus)

    # initialise learner
    learner = Learner(trainCorpus, useSupervision=useSupervision)

    if isEventCalculusNeeded(trainCorpus):
        trainCorpus.isEventCalculusNeeded = True

    # potentially can add this information into the parser.
    if choiceRulesPresent(trainCorpus):
        trainCorpus.choiceRulesPresent = True

    # train the data
    train(trainCorpus, reasoner, learner, numExamples)
    learningTime = time.time()

    # set hypotheses for testing corpus
    hypotheses = trainCorpus.getHypotheses()
    testCorpus.setHypotheses(hypotheses)

    # testing data loop
    numQuestions = 0
    numCorrect = 0

    print("TEST")
    # NEED TO REVISE THIS
    for story in testCorpus:
        for sentence in story:
            if isinstance(sentence, Question):
                numQuestions += 1
                answerToQuestion = reasoner.computeAnswer(sentence, story)
                if sentence.isCorrectAnswer(answerToQuestion):
                    numCorrect += 1
                else:
                    print(story)
                print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
                      sentence.getAnswer(), answerToQuestion, sentence.getHints())
                # for statement in story:
                #    print(statement.text, statement.getText())
    print("Number Correct: ", numCorrect)
    print("Number of Question: ", numQuestions)
    print("Accuracy: ", numCorrect / numQuestions)  # should theoretically be careful about dividing by zero
    print("Hypotheses: ", trainCorpus.getHypotheses())
    print("Parsing Time: ", parseEndTime - startTime)
    print("Learning Time: ", learningTime - parseEndTime)
    return numCorrect / numQuestions, parseEndTime - startTime, learningTime - parseEndTime


def train(corpus, reasoner, learner, numExamples):
    count = 0
    for story in corpus:
        for sentence in story:
            if isinstance(sentence, Question):
                if count >= numExamples:
                    return
                answerToQuestion = reasoner.computeAnswer(sentence, story)
                print(answerToQuestion, sentence.getAnswer(), sentence.getText(), sentence.getLineID())
                count += 1
                if not sentence.isCorrectAnswer(answerToQuestion):
                    learner.learn(sentence, story, answerToQuestion)
    print(corpus.nonEventCalculusExamples, corpus.eventCalculusExamples)


if __name__ == '__main__':
    # process data
    # trainingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa16_train.txt"
    # testingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa16_train.txt"
    trainingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task7_train"
    testingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task7_test"
    trainingCorpus = bAbIReader(trainingSet)
    testingCorpus = bAbIReader(testingSet)
    mainPipeline(trainingCorpus, testingCorpus, useSupervision=False)
