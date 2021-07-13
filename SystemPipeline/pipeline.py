from DatasetReader.bAbIReader import bAbIReader
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Question import Question
from TranslationalModule.bAbIParser import bAbIParser

if __name__ == '__main__':

    # hypotheses
    hypotheses = set()
    hypotheses.add("initiatedAt(be(V1, V2), V3):- happensAt(go(V1, V2), V3).")
    hypotheses.add("terminatedAt(be(V1, V2), V3):- happensAt(go(V1, V4), V3), holdsAt(be(V1, V2), V3).")

    # process data
    trainingReader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    testingReader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_test.txt")

    # get corpus
    corpus = trainingReader.corpus

    # initialise parser
    parser = bAbIParser(corpus)

    # initialise reasoner
    reasoner = Reasoner(corpus)

    # initialise learner
    learner = Learner(corpus)

    # training data loop
    for story in trainingReader.corpus:
        for sentence in story:
            parser.parse(story, sentence)
            if isinstance(sentence, Question):
                corpus.setHypotheses(hypotheses)
                answerToQuestion = reasoner.computeAnswer(sentence, story)
                # print(answerToQuestion, sentence.getAnswer())
                learner.learn(sentence, story, answerToQuestion)

    print(corpus.getHypotheses())

    # testing data loop
    numQuestions = 0
    numCorrect = 0
    testingReader.corpus.setHypotheses(hypotheses)
    for story in testingReader.corpus:
        for sentence in story:
            parser.parse(story, sentence)
            if isinstance(sentence, Question):
                numQuestions += 1
                answerToQuestion = reasoner.computeAnswer(sentence, story)
                # print(answerToQuestion, sentence.getAnswer())
                if sentence.isCorrectAnswer(answerToQuestion):
                    numCorrect += 1
    print("Number Correct: ", numCorrect)
    print("Number of Question: ", numQuestions)
    print("Accuracy: ", numCorrect / numQuestions)  # should theoretically be careful about dividing by zero
