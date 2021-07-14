import os

from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from TranslationalModule.basicParser import BasicParser


class Learner:
    def __init__(self, corpus):
        self.corpus = corpus

    def learn(self, question, story, answer):
        # check if the answer to the question is correct or not
        if question.isCorrectAnswer(answer):
            example = self.createBravePositiveExample(question, story)
            story.appendExample(example)

            # do not need to run a learning task here

        else:
            negativeExample = self.createBraveNegativeExample(question, story, answer)
            story.appendExample(negativeExample)

            # for bAbI dataset we can also create a positive example
            positiveExample = self.createBravePositiveExample(question, story)
            story.appendExample(positiveExample)

            # create learning file
            filename = self.createLearningFile()
            temp = open(filename, 'r')
            for line in temp:
                print(line)

            # use ILASP to complete learning task
            hypotheses = self.solveILASPtask(filename)

            # add the computed hypotheses to the corpus [note that we need to give new hypotheses each time]
            self.corpus.setHypotheses(hypotheses)

            # delete the file
            os.remove(filename)

    def createBravePositiveExample(self, question, story):
        positivePortion = question.createPartialInterpretation(question.getAnswer())

        # append all the extra event calculus and other predicates for the context aspect
        context = self.createContext(question, story)

        # put it altogether to form the positive example and add the positive example to the story.
        positiveExample = '#pos(' + positivePortion + ',{},' + context + ').'
        return positiveExample

    def createContext(self, question, story):
        context = '{'
        for statement in story:
            if statement == question:
                break
            if not isinstance(statement, Question):
                context = self.addEventCalculus(statement, context)
            context = self.addPredicates(statement, context)
        if context[-1] !='{':
            context += '.}\n'
        return context

    def addEventCalculus(self, question, context):
        if context[-1] != '{':
            context += '.\n'
        context += question.getEventCalculusRepresentation()
        return context

    def addPredicates(self, question, context):
        for predicate in question.getPredicates():
            if context[-1] != '{':
                context += '.\n'
            context += predicate

        return context

    def createBraveNegativeExample(self, question, story, answer):
        negativeInterpretation = question.createPartialInterpretation(answer)

        # append all the extra event calculus and other predicates for the context aspect
        context = self.createContext(question, story)

        # put it altogether to form the positive example and add the positive example to the story.
        negativeExample = '#pos(' + '{},' + negativeInterpretation + ',' + context + ').'
        return negativeExample

    def createLearningFile(self):
        filename = '/tmp/learningFile.las'
        temp = open(filename, 'w')
        # add in the background knowledge
        for rule in self.corpus.backgroundKnowledge:
            temp.write(rule)
            temp.write('\n')

        # add in the mode bias
        for bias in self.corpus.modeBias:
            temp.write(bias)
            temp.write('\n')

        # add in examples for the stories thus far
        for story in self.corpus:
            for example in story.getExamples():
                temp.write(example)
                temp.write('\n')

        temp.write("#maxv(4).")
        temp.write('\n')

        temp.close()
        return filename

    def solveILASPtask(self, filename):
        command = "ILASP -q -nc -ml=2 --version=4 " + filename
        output = os.popen(command).read()
        return self.processILASP(output)

    def processILASP(self, output):
        lines = output.split('\n')
        return set([line for line in lines if line])



if __name__ == '__main__':
    # process data
    reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")

    # get corpus
    corpus = reader.corpus

    # initialise parser
    parser = BasicParser(corpus)

    # learner
    learner = Learner(corpus)
    for story in reader.corpus:
        statements = story.getSentences()
        for statement in statements:
            parser.parse(statements, statement)
            if isinstance(statement, Question):
                learner.learn(statement, story, "bedroom")
    print(corpus.getHypotheses())
