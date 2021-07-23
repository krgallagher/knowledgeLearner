from DatasetReader.bAbIReader import bAbIReader
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Question import Question
from TranslationalModule.ExpressivityChecker import isEventCalculusNeeded
from TranslationalModule.basicParser import BasicParser

if __name__ == '__main__':
    # process data
    #trainingReader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa6_yes-no-questions_train.txt")
    #testingReader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa6_yes-no-questions_test.txt")
    trainingReader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task13_train")
    testingReader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task13_test")

    # get corpus
    corpus = trainingReader.corpus

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


    # train the data
    for story in corpus:
        for sentence in story:
            if isinstance(sentence, Question):
                answerToQuestion = reasoner.computeAnswer(sentence, story, corpus.isEventCalculusNeeded)
                print(answerToQuestion, sentence.getAnswer(), sentence.getText(), sentence.getLineID())
                learner.learn(sentence, story, answerToQuestion, corpus.isEventCalculusNeeded)

    # set hypotheses for testing corpus
    hypotheses = corpus.getHypotheses()
    testingReader.corpus.setHypotheses(hypotheses)

    # testing data loop
    numQuestions = 0
    numCorrect = 0

    print("TEST")
    for story in testingReader.corpus:
        for sentence in story:
            parser.parse(story, sentence)
            if isinstance(sentence, Question):
                numQuestions += 1
                answerToQuestion = reasoner.computeAnswer(sentence, story, corpus.isEventCalculusNeeded)
                if sentence.isCorrectAnswer(answerToQuestion):
                    numCorrect += 1
                print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
                      sentence.getAnswer(), answerToQuestion)
    print("Number Correct: ", numCorrect)
    print("Number of Question: ", numQuestions)
    print("Accuracy: ", numCorrect / numQuestions)  # should theoretically be careful about dividing by zero
    print("Hypotheses: ", corpus.getHypotheses())
