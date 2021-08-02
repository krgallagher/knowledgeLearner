from DatasetReader.bAbIReader import bAbIReader
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Question import Question
from TranslationalModule.ChoiceRulesChecker import choiceRulesPresent
from TranslationalModule.ExpressivityChecker import isEventCalculusNeeded
from TranslationalModule.basicParser import BasicParser


def mainPipeline(trainCorpus, testCorpus, numExamples=10000):
    # initialise parser
    parser = BasicParser(trainCorpus, testCorpus)
    # initialise reasoner
    reasoner = Reasoner(trainCorpus)
    # initialise learner
    learner = Learner(trainCorpus, useHints=True)

    if isEventCalculusNeeded(trainCorpus):
        trainCorpus.isEventCalculusNeeded = True
    # potentially can add this information into the parser.
    if choiceRulesPresent(trainCorpus):
        trainCorpus.choiceRulesPresent = True

    # train the data
    train(trainCorpus, reasoner, learner, numExamples)
    # set hypotheses for testing corpus
    hypotheses = trainCorpus.getHypotheses()
    testCorpus.setHypotheses(hypotheses)
    # testing data loop
    numQuestions = 0
    numCorrect = 0
    print("TEST")
    #NEED TO REVISE THIS
    for story in testCorpus:
        for sentence in story:
            if isinstance(sentence, Question):
                numQuestions += 1
                answerToQuestion = reasoner.computeAnswer(sentence, story, trainCorpus.isEventCalculusNeeded)
                if sentence.isCorrectAnswer(answerToQuestion):
                    numCorrect += 1
                print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
                      sentence.getAnswer(), answerToQuestion)
    print("Number Correct: ", numCorrect)
    print("Number of Question: ", numQuestions)
    print("Accuracy: ", numCorrect / numQuestions)  # should theoretically be careful about dividing by zero
    print("Hypotheses: ", trainCorpus.getHypotheses())
    return numCorrect / numQuestions


def train(corpus, reasoner, learner, numExamples):
    count = 0
    for story in corpus:
        for sentence in story:
            if isinstance(sentence, Question):
                if count >= numExamples:
                    return
                answerToQuestion = reasoner.computeAnswer(sentence, story, corpus.isEventCalculusNeeded)
                print(answerToQuestion, sentence.getAnswer(), sentence.getText(), sentence.getLineID())
                learner.learn(sentence, story, answerToQuestion, corpus.isEventCalculusNeeded)
                count += 1


if __name__ == '__main__':
    # process data
    #trainingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa6_yes-no-questions_train.txt"
    #testingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa6_yes-no-questions_test.txt"
    trainingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task18_train"
    testingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task18_test"
    trainingCorpus = bAbIReader(trainingSet)
    testingCorpus = bAbIReader(testingSet)
    mainPipeline(trainingCorpus, testingCorpus)
