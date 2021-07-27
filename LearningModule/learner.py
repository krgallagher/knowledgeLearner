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
    def __init__(self, corpus):
        self.corpus = corpus

    def learn(self, question: Question, story: Story, answer, eventCalculusNeeded=True):

        self.updateModeBias(story, question)

        # check if the answer to the question is correct or not
        if question.isCorrectAnswer(answer):
            if "where" in question.getText().lower() or "what" in question.getText().lower():
                example = self.createPositiveExample(question, story, eventCalculusNeeded)
                # example = self.createBravePositiveExample(question, story, eventCalculusNeeded)
            else:
                if "yes" in answer or "maybe" in answer:
                    example = self.createPositiveExample(question, story, eventCalculusNeeded)
                    # example = self.createBravePositiveExample(question, story, eventCalculusNeeded)
                else:
                    example = self.createNegativeExample(question, story, eventCalculusNeeded)
                    # example = self.createBraveNegativeExample(question, story, eventCalculusNeeded)
            story.appendExample(example)


        else:
            if "where" in question.getText().lower() or "what" in question.getText().lower():
                if len(answer) == 0:
                    example = self.createPositiveExample(question, story, eventCalculusNeeded)
                    # example = self.createBravePositiveExample(question, story, eventCalculusNeeded)
                else:
                    example = self.createNegativeExample(question, story, eventCalculusNeeded, answer)
                    # example = self.createBraveNegativeExample(question, story, eventCalculusNeeded, answer)
            else:
                if "yes" in question.getAnswer() or "maybe" in question.getAnswer():
                    example = self.createPositiveExample(question, story, eventCalculusNeeded)
                    # example = self.createBravePositiveExample(question, story, eventCalculusNeeded)
                else:
                    example = self.createNegativeExample(question, story, eventCalculusNeeded)
                    # example = self.createBraveNegativeExample(question, story, eventCalculusNeeded)
            story.appendExample(example)


            unsatisfiable = set()
            unsatisfiable.add("UNSATISFIABLE")

            filename = self.createLearningFile(question, story, eventCalculusNeeded, False)
            #temp = open(filename, 'r')
            #for line in temp:
            #    print(line)

            hypotheses = self.solveILASPtask(filename)

            print("HYPOTHESES", hypotheses)
            if hypotheses != unsatisfiable:
                self.corpus.addHypotheses(hypotheses)

            print("CURRENT HYPOTHESES: ", self.corpus.getHypotheses())

            # try to first add the hypotheses previously learned and the mode bias that is only relevant to the
            # example that was wrong

            # delete the file
            # might not want to delete the file in case information is cached.
            # os.remove(filename)

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
        for i in range(0, len(representation)):
            rule = createChoiceRule(representation[i])
            if context[-1] != '{' and context[-1] != '\n':
                context += '.\n'
            context += rule
        return context

    def addPredicates(self, question, context):
        for predicate in question.getPredicates():
            if context[-1] != '{':
                context += '.\n'
            context += predicate
        return context

    def createLearningFile(self, question: Question, story: Story, eventCalculusNeeded, withOldHypotheses):
        # filename = '/tmp/learningFile.las'
        filename = "/Users/katiegallagher/Desktop/IndividualProject/learningFile.las"
        temp = open(filename, 'w')
        # add in the background knowledge only if using the event calculus
        #if eventCalculusNeeded:
        for rule in self.corpus.backgroundKnowledge:
            temp.write(rule)
            temp.write('\n')

        if withOldHypotheses:
            for hypothesis in self.corpus.getHypotheses():
                temp.write(hypothesis)
                temp.write('\n')

            for bias in self.getRelevantModeBias(story, question):
                temp.write(bias)
                temp.write('\n')
        else:
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
            for i in range(0, len(modeBiasFluents)):
                for j in range(0, len(modeBiasFluents[i])):
                    modeBiasFluent = modeBiasFluents[i][j]
                    predicate = modeBiasFluent.split('(')[0].split('_')[0]
                    if predicate == "be":
                        modeBias = self.generateBeBias(modeBiasFluent, currentStatement)
                    else:
                        modeBias = self.generateNonBeBias(modeBiasFluent)
                    self.corpus.updateModeBias(modeBias)

    def getRelevantModeBias(self, story: Story, statement: Statement):
        print("GeTTiNG relevant mode bias")
        relevantModeBias = set()
        for index in range(0, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            if isinstance(currentStatement, Question) and currentStatement != statement:
                pass
            else:
                modeBiasFluents = currentStatement.getModeBiasFluents()
                print("MODE bias fluents:", modeBiasFluents)
                for i in range(0, len(modeBiasFluents)):
                    for j in range(0, len(modeBiasFluents[i])):
                        modeBiasFluent = modeBiasFluents[i][j]
                        predicate = modeBiasFluent.split('(')[0].split('_')[0]
                        if predicate == "be":
                            modeBias = self.generateBeBias(modeBiasFluent, currentStatement)
                        else:
                            modeBias = self.generateNonBeBias(modeBiasFluent)
                        relevantModeBias.update(modeBias)
            print(relevantModeBias)
        return relevantModeBias

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
    corpus = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")

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
