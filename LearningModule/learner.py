import os
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.EventCalculus import initiatedAt, terminatedAt, holdsAt, happensAt
from TranslationalModule.basicParser import BasicParser, varWrapping
from Utilities.ILASPSyntax import createTimeRange, modeHWrapping, modeBWrapping


class Learner:
    def __init__(self, corpus):
        self.corpus = corpus

    def learn(self, question: Question, story: Story, answer, eventCalculusNeeded=True):

        self.updateModeBias(story, question)

        # check if the answer to the question is correct or not
        if question.isCorrectAnswer(answer):
            if "where" in question.getText().lower() or "what" in question.getText().lower():
                example = self.createBravePositiveExample(question, story, eventCalculusNeeded)
            else:
                if "yes" in answer:
                    example = self.createBravePositiveExample(question, story, eventCalculusNeeded)
                else:
                    example = self.createBraveNegativeExample(question, story, eventCalculusNeeded)
            story.appendExample(example)

            # do not need to run a learning task here

        else:
            if "where" in question.getText().lower() or "what" in question.getText().lower():
                if len(answer) == 0:
                    example = self.createBravePositiveExample(question, story, eventCalculusNeeded)
                else:
                    example = self.createBraveNegativeExample(question, story, eventCalculusNeeded, answer)
            else:
                if "yes" in question.getAnswer():
                    example = self.createBravePositiveExample(question, story, eventCalculusNeeded)
                else:

                    example = self.createBraveNegativeExample(question, story, eventCalculusNeeded)
            story.appendExample(example)

            # for bAbI dataset we can also create a positive example
            # positiveExample = self.createBravePositiveExample(question, story)
            # story.appendExample(positiveExample)

            # create learning file
            filename = self.createLearningFile(eventCalculusNeeded)
            temp = open(filename, 'r')
            for line in temp:
                print(line)

            # use ILASP to complete learning task
            hypotheses = self.solveILASPtask(filename)
            print("HYPOTHESES:", hypotheses)

            # If the hypotheses are satisfiable, then add the computed hypotheses to the corpus
            unsatisfiable = set()
            unsatisfiable.add("UNSATISFIABLE")
            if hypotheses != unsatisfiable:
                self.corpus.setHypotheses(hypotheses)

            # delete the file
            # might not want to delete the file in case information is cached.
            # os.remove(filename)

    def createBravePositiveExample(self, question: Question, story: Story, eventCalculusNeeded):
        positivePortion = question.createPartialInterpretation(question.getAnswer(), eventCalculusNeeded)

        # append all the extra event calculus and other predicates for the context aspect
        context = self.createContext(question, story, eventCalculusNeeded)

        # put it altogether to form the positive example and add the positive example to the story.
        positiveExample = '#pos(' + positivePortion + ',{},' + context + ').'
        return positiveExample

    def createBraveNegativeExample(self, question: Question, story: Story, eventCalculusNeeded, answer=[]):
        negativeInterpretation = question.createPartialInterpretation(answer, eventCalculusNeeded)

        # append all the extra event calculus and other predicates for the context aspect
        context = self.createContext(question, story, eventCalculusNeeded)

        # put it altogether to form the positive example and add the positive example to the story.
        negativeExample = '#pos(' + '{},' + negativeInterpretation + ',' + context + ').'
        return negativeExample

    def createContext(self, question: Question, story: Story, eventCalculusNeeded):
        context = '{'
        for statement in story:
            if not isinstance(statement, Question):
                context = self.addRepresentation(statement, context, eventCalculusNeeded)
            context = self.addPredicates(statement, context)
            if statement == question:
                break
        if context[-1] != '{':
            context += '.\n'
            if eventCalculusNeeded:
                context += createTimeRange(question.getLineID())
                context += '.\n'
        context += '}\n'
        return context

    def addRepresentation(self, statement: Statement, context, eventCalculusNeeded):
        if eventCalculusNeeded:
            representation = statement.getEventCalculusRepresentation()
        else:
            representation = statement.getFluents()
        for predicate in representation:
            if context[-1] != '{' and context[-1] != '\n':
                context += '.\n'
            context += predicate
            # context += '\n'
        return context

    def addPredicates(self, question, context):
        for predicate in question.getPredicates():
            if context[-1] != '{':
                context += '.\n'
            context += predicate
        return context

    def createLearningFile(self, eventCalculusNeeded):
        # filename = '/tmp/learningFile.las'
        filename = "/Users/katiegallagher/Desktop/IndividualProject/learningFile.las"
        temp = open(filename, 'w')
        # add in the background knowledge only if using the event calculus
        if eventCalculusNeeded:
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

        # might want to make this so it starts with 4 variables and then gradually increases.
        if eventCalculusNeeded:
            temp.write("#maxv(4)")
        else:
            temp.write("#maxv(3)")
        temp.write('.\n')

        temp.close()
        return filename

    def solveILASPtask(self, filename):
        # command = "FastLAS --nopl" + filename
        command = "ILASP -q -nc -ml=2 --version=4 " + filename
        output = os.popen(command).read()
        return self.processILASP(output)

    def processILASP(self, output):
        lines = output.split('\n')
        return set([line for line in lines if line])

    def updateModeBias(self, story: Story, statement: Statement):
        for index in range(0, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            modeBiasFluents = currentStatement.getModeBiasFluents()
            for modeBiasFluent in modeBiasFluents:
                predicate = modeBiasFluent.split('(')[0].split('_')[0]
                if predicate == "be":
                    modeBias = self.generateBeBias(modeBiasFluent, currentStatement)
                else:
                    modeBias = self.generateNonBeBias(modeBiasFluent)
            self.corpus.updateModeBias(modeBias)

    def generateBeBias(self, modeBiasFluent, statement: Statement):
        bias = set()
        if self.corpus.isEventCalculusNeeded:
            time = varWrapping("time")
            initiated = initiatedAt(modeBiasFluent, time)
            holds = holdsAt(modeBiasFluent, time)
            terminated = terminatedAt(modeBiasFluent, time)
            if isinstance(statement, Question):
                bias.add(modeHWrapping(initiated))
                bias.add(modeHWrapping(terminated))
            else:
                bias.add(modeBWrapping(initiated))
            bias.add(modeBWrapping(holds))
        else:
            if isinstance(statement, Question):
                bias.add(modeHWrapping(modeBiasFluent))
            else:
                bias.add(modeBWrapping(modeBiasFluent))
        return bias

    def generateNonBeBias(self, modeBiasFluent):
        bias = set()
        if self.corpus.isEventCalculusNeeded:
            time = varWrapping("time")
            happens = happensAt(modeBiasFluent, time)
            bias.add(modeBWrapping(happens))
        else:
            bias.add(modeBWrapping(modeBiasFluent))
        return bias


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
