from DatasetReader.bAbIReader import bAbIReader
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Question import Question
from TranslationalModule.ChoiceRulesChecker import choiceRulesPresent
from TranslationalModule.DatasetParser import DatasetParser
from TranslationalModule.ExpressivityChecker import isEventCalculusNeeded


def mainPipeline(trainCorpus, testCorpus, numExamples=10000):
    # initialise parser
    DatasetParser(trainCorpus, testCorpus)

    # initialise reasoner
    reasoner = Reasoner(trainCorpus)

    # initialise learner
    learner = Learner(trainCorpus, useHints=False)

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
    # NEED TO REVISE THIS
    for story in testCorpus:
        for sentence in story:
            if isinstance(sentence, Question):
                numQuestions += 1
                answerToQuestion = reasoner.computeAnswer(sentence, story, trainCorpus.isEventCalculusNeeded)
                if sentence.isCorrectAnswer(answerToQuestion):
                    numCorrect += 1
                else:
                    print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
                          sentence.getAnswer(), answerToQuestion, sentence.getHints())
                    for statement in story:
                        print(statement.text, statement.getText())
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
    # trainingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa16_basic-induction_train.txt"
    # testingSet = "/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa16_basic-induction_train.txt"
    trainingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task15_train"
    testingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task15_test"
    trainingCorpus = bAbIReader(trainingSet)
    testingCorpus = bAbIReader(testingSet)
    mainPipeline(trainingCorpus, testingCorpus)
