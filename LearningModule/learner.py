import os
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.EventCalculus import initiatedAt, terminatedAt, holdsAt, happensAt
from TranslationalModule.ExpressivityChecker import createChoiceRule
from TranslationalModule.basicParser import BasicParser, varWrapping
from Utilities.ILASPSyntax import createTimeRange, modeHWrapping, modeBWrapping


class Learner:
    def __init__(self, corpus, filename="/Users/katiegallagher/Desktop/IndividualProject/learningFile.las",
                 cachingFile="/Users/katiegallagher/Desktop/IndividualProject/cachingFile.las"):
        # will probably eventually want to make the default be in the tmp bin, but this is okay for now I think
        self.filename = filename
        self.cachingFile = cachingFile
        self.corpus = corpus
        self.oldModeBias = set()
        self.previousStoryIndexForIncorrectQuestion = 0  # default to the first story
        self.previousExampleAddedIndex = 0  # the last index that has been added for a positive/negative example
        # need to store the index

    def learn(self, question: Question, story: Story, answer, eventCalculusNeeded=True):
        # check if the answer to the question is correct or not
        if question.isCorrectAnswer(answer):
            if "where" in question.getText().lower() or "what" in question.getText().lower():
                example = self.createPositiveExample(question, story, eventCalculusNeeded)
            else:
                if "yes" in answer or "maybe" in answer:
                    example = self.createPositiveExample(question, story, eventCalculusNeeded)
                else:
                    example = self.createNegativeExample(question, story, eventCalculusNeeded)
            story.appendExample(example)
        else:
            if "where" in question.getText().lower() or "what" in question.getText().lower():
                if answer == ["nothing"]:
                    example = self.createPositiveExample(question, story, eventCalculusNeeded)
                else:
                    example = self.createNegativeExample(question, story, eventCalculusNeeded, answer)
            else:
                if "yes" in question.getAnswer() or "maybe" in question.getAnswer():
                    example = self.createPositiveExample(question, story, eventCalculusNeeded)
                else:
                    example = self.createNegativeExample(question, story, eventCalculusNeeded)
            story.appendExample(example)

            # possibly refactor this bit.
            unsatisfiable = set()
            unsatisfiable.add("UNSATISFIABLE")

            # store the old mode bias
            self.oldModeBias = self.corpus.modeBias.copy()

            # update the old mode bias.
            self.updateModeBias(story, question)

            if self.oldModeBias == self.corpus.modeBias:
                self.appendExamplesToLearningFile(story)
            else:
                if os.path.exists(self.cachingFile):
                    os.remove(self.cachingFile)
                self.createLearningFile(eventCalculusNeeded)

            # update the index of the previous story to have a question wrong.
            self.previousStoryIndexForIncorrectQuestion = self.corpus.getIndex(story)

            file = open(self.filename, 'r')
            for line in file:
                print(line)

            hypotheses = self.solveILASPtask()

            print("HYPOTHESES", hypotheses)
            if hypotheses != unsatisfiable:
                self.corpus.addHypotheses(hypotheses)

            print("CURRENT HYPOTHESES: ", self.corpus.getHypotheses())

    # TODO uncomment this later on and remove the pass
    def __del__(self):
        # delete file from computer
        # os.remove(self.filename)
        pass

    def createPositiveExample(self, question, story, eventCalculusNeeded):
        if "maybe" in question.getAnswer():
            return self.createBravePositiveExample(question, story, eventCalculusNeeded)
        if self.corpus.choiceRulesPresent:
            return self.createCautiousPositiveExample(question, story, eventCalculusNeeded)
        return self.createBravePositiveExample(question, story, eventCalculusNeeded)

    def createNegativeExample(self, question, story, eventCalculusNeeded, answer=[]):
        if self.corpus.choiceRulesPresent:
            return self.createCautiousNegativeExample(question, story, eventCalculusNeeded, answer)
        return self.createBraveNegativeExample(question, story, eventCalculusNeeded, answer)

    def createBravePositiveExample(self, question: Question, story: Story, eventCalculusNeeded):
        positivePortion = question.createPartialInterpretation(question.getAnswer(), eventCalculusNeeded)

        context = self.createContext(question, story, eventCalculusNeeded)

        positiveExample = '#pos(' + positivePortion + ',{},' + context + ').'
        return positiveExample

    def createBraveNegativeExample(self, question: Question, story: Story, eventCalculusNeeded, answer=[]):
        negativeInterpretation = question.createPartialInterpretation(answer, eventCalculusNeeded)

        # append all the extra event calculus and other predicates for the context aspect
        context = self.createContext(question, story, eventCalculusNeeded)

        # put it altogether to form the positive example and add the positive example to the story.
        negativeExample = '#pos(' + '{},' + negativeInterpretation + ',' + context + ').'
        return negativeExample

    def createCautiousPositiveExample(self, question: Question, story: Story, eventCalculusNeeded):
        positivePortion = question.createPartialInterpretation(question.getAnswer(), eventCalculusNeeded)

        # append all the extra event calculus and other predicates for the context aspect
        context = self.createContext(question, story, eventCalculusNeeded)

        # put it altogether to form the positive example and add the positive example to the story.
        positiveExample = '#neg(' + '{},' + positivePortion + "," + context + ').'
        return positiveExample

    def createCautiousNegativeExample(self, question: Question, story: Story, eventCalculusNeeded, answer=[]):
        negativeInterpretation = question.createPartialInterpretation(answer, eventCalculusNeeded)

        # append all the extra event calculus and other predicates for the context aspect
        context = self.createContext(question, story, eventCalculusNeeded)

        # put it altogether to form the positive example and add the positive example to the story.
        negativeExample = '#neg(' + negativeInterpretation + ',{},' + context + ').'
        return negativeExample

    def createContext(self, question: Question, story: Story, eventCalculusNeeded):
        predicates = set()
        context = '{'
        for statement in story:
            if not isinstance(statement, Question):
                context = self.addRepresentation(statement, context, eventCalculusNeeded)
            predicates.update(statement.getPredicates())
            if statement == question:
                break
        context = self.addPredicates(predicates, context)
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
        for i in range(0, len(representation)):
            rule = createChoiceRule(representation[i])
            if context[-1] != '{' and context[-1] != '\n':
                context += '.\n'
            context += rule
        return context

    def addPredicates(self, predicates, context):
        for predicate in predicates:
            if context[-1] != '{':
                context += '.\n'
            context += predicate
        return context

    def createLearningFile(self, eventCalculusNeeded):
        file = open(self.filename, 'w')
        # add in the background knowledge only if using the event calculus
        # if eventCalculusNeeded:
        for rule in self.corpus.backgroundKnowledge:
            file.write(rule)
            file.write('\n')

        # add in the mode bias
        for bias in self.corpus.modeBias:
            file.write(bias)
            file.write('\n')

        # might want to make this so it starts with 4 variables and then gradually increases.
        if eventCalculusNeeded:
            file.write("#maxv(4)")
        else:
            file.write("#maxv(3)")
        file.write('.\n')

        # add in examples for the stories thus far
        for story in self.corpus:
            self.addExamplesFromStory(file, story)
        file.close()

    def appendExamplesToLearningFile(self, story: Story):
        file = open(self.filename, 'a')
        lastStory = self.corpus.get(self.previousStoryIndexForIncorrectQuestion)
        for index in range(self.previousExampleAddedIndex + 1, len(lastStory.examples) - 1):
            example = lastStory.examples[index]
            file.write(example)
            file.write('\n')

        for index in range(self.previousStoryIndexForIncorrectQuestion + 1, self.corpus.getIndex(story)):
            previousStory = self.corpus.stories[index]
            self.addExamplesFromStory(file, previousStory)

        self.addExamplesFromStory(file, story)
        # TODO need to move this up
        self.previousExampleAddedIndex = len(story.examples) - 1
        file.close()

    def addExamplesFromStory(self, file, story: Story):
        for example in story.getExamples():
            file.write(example)
            file.write('\n')

    def solveILASPtask(self):
        # command = "FastLAS --nopl" + filename
        command = "ILASP -q -nc -ml=2 --version=4 --cache-path=" + self.cachingFile + " " + self.filename
        output = os.popen(command).read()
        return self.processILASP(output)

    def processILASP(self, output):
        lines = output.split('\n')
        return set([line for line in lines if line])

    def updateModeBias(self, story: Story, question: Statement):
        # add the mode bias for all the stories so far
        for storyIndex in range(self.previousStoryIndexForIncorrectQuestion, self.corpus.getIndex(story)):
            for sentence in self.corpus.stories[storyIndex]:
                self.addStatementModeBias(sentence)

        # add the mode bias for current story
        for index in range(0, story.getIndex(question) + 1):
            currentStatement = story.get(index)
            self.addStatementModeBias(currentStatement)

    def addStatementModeBias(self, statement):
        modeBiasFluents = statement.getModeBiasFluents()
        for i in range(0, len(modeBiasFluents)):
            for j in range(0, len(modeBiasFluents[i])):
                modeBiasFluent = modeBiasFluents[i][j]
                predicate = modeBiasFluent.split('(')[0].split('_')[0]
                if predicate == "be" or isinstance(statement, Question):
                    modeBias = self.generateBeAndQuestionBias(modeBiasFluent, statement)
                else:
                    modeBias = self.generateNonBeBias(modeBiasFluent, statement)
                self.corpus.updateModeBias(modeBias)

    def generateBeAndQuestionBias(self, modeBiasFluent, statement: Statement):
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

    def generateNonBeBias(self, modeBiasFluent, statement: Statement):
        bias = set()
        if self.corpus.isEventCalculusNeeded:
            time = varWrapping("time")
            happens = happensAt(modeBiasFluent, time)
            bias.add(modeBWrapping(happens))
        else:
            if isinstance(statement, Question):
                bias.add(modeHWrapping(modeBiasFluent))
            else:
                bias.add(modeBWrapping(modeBiasFluent))
        return bias


if __name__ == '__main__':
    # process data
    corpus = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task18_train")

    # initialise parser
    parser = BasicParser(corpus)

    # learner
    learner = Learner(corpus)
    for story in corpus:
        statements = story.getSentences()
        for statement in statements:
            parser.parse(statements, statement)
            if isinstance(statement, Question):
                learner.learn(statement, story, "bedroom")
    print(corpus.getHypotheses())
