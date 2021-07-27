from DatasetReader.bAbIReader import bAbIReader
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Question import Question
from TranslationalModule.ChoiceRulesChecker import choiceRulesPresent
from TranslationalModule.ExpressivityChecker import isEventCalculusNeeded
from TranslationalModule.basicParser import BasicParser


def mainPipeline(trainer, tester, numExamples=10000):
    # get corpus
    corpus = trainer.corpus
    # initialise parser
    parser = BasicParser(corpus)
    # initialise reasoner
    reasoner = Reasoner(corpus)
    # initialise learner
    learner = Learner(corpus)
    # training data loop
    # parse through all of the data
    for story in corpus:
        for sentence in story:
            parser.parse(story, sentence)
    if isEventCalculusNeeded(corpus):
        corpus.isEventCalculusNeeded = True
    # potentially can add this information into the parser.
    if choiceRulesPresent(corpus):
        corpus.choiceRulesPresent = True

    # train the data
    train(corpus, reasoner, learner, numExamples)
    # set hypotheses for testing corpus
    hypotheses = corpus.getHypotheses()
    # testing data loop
    numQuestions = 0
    numCorrect = 0
    #print("TEST")
    for story in tester.corpus:
        for sentence in story:
            parser.parse(story, sentence)
            if isinstance(sentence, Question):
                numQuestions += 1
                answerToQuestion = reasoner.computeAnswer(sentence, story, corpus.isEventCalculusNeeded)
                if sentence.isCorrectAnswer(answerToQuestion):
                    numCorrect += 1
                print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(), sentence.getAnswer(), answerToQuestion)
    #print("Number Correct: ", numCorrect)
    #print("Number of Question: ", numQuestions)
    #print("Accuracy: ", numCorrect / numQuestions)  # should theoretically be careful about dividing by zero
    #print("Hypotheses: ", corpus.getHypotheses())
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
    # trainingReader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa6_yes-no-questions_train.txt")
    # testingReader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa6_yes-no-questions_test.txt")
    trainingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train"
    testingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_test"
    trainingReader = bAbIReader(trainingSet)
    testingReader = bAbIReader(testingSet)
    mainPipeline(trainingReader, testingReader)
