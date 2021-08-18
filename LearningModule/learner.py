import os
import re
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.ExpressivityChecker import createChoiceRule
from Utilities.ILASPSyntax import createTimeRange, createBias


def isSatisfiable(hypotheses):
    unsatisfiable = set()
    unsatisfiable.add("UNSATISFIABLE")
    return unsatisfiable != hypotheses


def getRepresentationFromModeBias(rule):
    substitution = re.compile("#mode.\((.*)\)\.")
    return re.sub(substitution, "\\1", rule)


def numberOfConstantArguments(representation):
    return representation.count('const')


def numberOfNonConstantArguments(representation):
    return representation.count('var')


def createConstraint(representation):
    timeSubstitution = re.compile("var\(time\)")
    representation = re.sub(timeSubstitution, "_", representation)
    substitution = re.compile("var\([^\)]*\)")
    return re.sub(substitution, "V1", representation)


def hasConstantType(constant, representation):
    constantType = constant.split('(')[1].split(',')[0]
    constantArgument = "const(" + constantType + ")"
    return constantArgument in representation


def substituteConstant(constant, representation):
    constantName = constant.split(',')[1][:-1]
    constantType = constant.split('(')[1].split(',')[0]
    constantArgument = "const(" + constantType + ")"
    return representation.replace(constantArgument, constantName)


class Learner:
    def __init__(self, corpus, filename="/Users/katiegallagher/Desktop/IndividualProject/learningFile.las",
                 cachingFile="/Users/katiegallagher/Desktop/IndividualProject/cachingFile.las", useSupervision=False):
        self.filename = filename
        self.cachingFile = cachingFile
        self.corpus = corpus
        self.useSupervision = useSupervision
        self.eventCalculusNeededPreviously = False
        self.currentExamplesIndex = 0

    def learn(self, question: Question, story: Story, answer, createNewLearningFile=False):
        if question.isYesNoMaybeQuestion():
            if "yes" in question.getAnswer() or "maybe" in question.getAnswer():
                self.createPositiveExample(question, story)
            else:
                self.createNegativeExample(question, story)
        else:
            # TODO determine if I need these
            if answer == ["nothing"] or answer == ['none'] or not answer:
                self.createPositiveExample(question, story)
            else:
                self.createNegativeExample(question, story, answer)

        if self.eventCalculusNeededPreviously != self.corpus.isEventCalculusNeeded or not os.path.exists(
                self.filename) or createNewLearningFile:
            if os.path.exists(self.cachingFile):
                os.remove(self.cachingFile)
            self.createLearningFile()
        else:
            self.appendExamplesToLearningFile()

        file = open(self.filename, 'r')
        for line in file:
            print(line)

        hypotheses = self.solveILASPTask()

        print("HYPOTHESES", hypotheses)
        if isSatisfiable(hypotheses):
            self.corpus.setHypotheses(hypotheses)

        self.eventCalculusNeededPreviously = self.corpus.isEventCalculusNeeded

        print("CURRENT HYPOTHESES: ", self.corpus.getHypotheses())

    def __del__(self):
        os.remove(self.filename)
        os.remove(self.cachingFile)

    def createPositiveExample(self, question: Question, story: Story):
        if "maybe" in question.getAnswer():
            self.createBravePositiveExample(question, story)
        elif self.corpus.choiceRulesPresent:
            self.createCautiousPositiveExample(question, story)
        else:
            self.createBravePositiveExample(question, story)

    def createNegativeExample(self, question: Question, story: Story, answer=None):
        if self.corpus.choiceRulesPresent:
            self.createCautiousNegativeExample(question, story, answer)
        else:
            self.createBraveNegativeExample(question, story, answer)

    def createBravePositiveExample(self, question: Question, story: Story):
        positiveNonECPortion, positiveECPortion = question.createPartialInterpretation(question.getAnswer())
        nonECContext, ECContext = self.createContext(question, story)
        positiveNonECExample = '#pos(' + positiveNonECPortion + ',{},' + nonECContext + ').'
        positiveECExample = '#pos(' + positiveECPortion + ',{},' + ECContext + ').'
        self.addExamples(positiveNonECExample, positiveECExample)

    def createCautiousPositiveExample(self, question: Question, story: Story):
        positiveNonECPortion, positiveECPortion = question.createPartialInterpretation(question.getAnswer())
        nonECContext, ECContext = self.createContext(question, story)
        positiveNonECExample = '#neg(' + '{},' + positiveNonECPortion + "," + nonECContext + ').'
        positiveECExample = '#neg(' + '{},' + positiveECPortion + "," + ECContext + ').'
        self.addExamples(positiveNonECExample, positiveECExample)

    def createBraveNegativeExample(self, question: Question, story: Story, answers=None):
        positiveNonECPortion, positiveECPortion = '{}', '{}'
        if not answers:
            negativeNonECPortion, negativeECPortion = question.createPartialInterpretation()
        else:
            negativeNonECPortion, negativeECPortion = '{}', '{}'
            for answer in answers:
                if question.isCorrectAnswer([answer]):
                    positiveNonECPortion, positiveECPortion = question.createPartialInterpretation([answer])
                else:
                    negativeNonECPortion, negativeECPortion = question.createPartialInterpretation([answer])
            if positiveNonECPortion == '{}' and question.answer != ["nothing"]:
                positiveNonECPortion, positiveECPortion = question.createPartialInterpretation(question.getAnswer())

        nonECContext, ECContext = self.createContext(question, story)
        negativeNonECExample = '#pos(' + positiveNonECPortion + ',' + negativeNonECPortion + ',' + nonECContext + ').'
        negativeECExample = '#pos(' + positiveECPortion + ',' + negativeECPortion + ',' + ECContext + ').'
        self.addExamples(negativeNonECExample, negativeECExample)

    def createCautiousNegativeExample(self, question: Question, story: Story, answer=None):
        negativeNonECPortion, negativeECPortion = question.createPartialInterpretation(answer)
        nonECContext, ECContext = self.createContext(question, story)
        negativeNonECExample = '#neg(' + negativeNonECPortion + ',{},' + nonECContext + ').'
        negativeECExample = '#neg(' + negativeECPortion + ',{},' + ECContext + ').'
        self.addExamples(negativeNonECExample, negativeECExample)

    def createContext(self, question: Question, story: Story):
        predicates = set()
        nonECContext, ECContext = '{', '{'
        if self.useSupervision:
            for hint in question.getHints():
                statement = story.get(int(hint) - 1)
                nonECContext, ECContext = self.addRepresentation(statement, nonECContext, ECContext)
                predicates.update(statement.getPredicates())
        else:
            for statement in story:
                if not isinstance(statement, Question):
                    nonECContext, ECContext = self.addRepresentation(statement, nonECContext, ECContext)
                predicates.update(statement.getPredicates())
                if statement == question:
                    break
        nonECContext, ECContext = self.addPredicates(predicates, nonECContext), self.addPredicates(predicates,
                                                                                                   ECContext)
        if nonECContext[-1] != '{':
            nonECContext += '.\n'
            ECContext += '.\n'
            ECContext += createTimeRange(question.getLineID())
            ECContext += '.\n'
        nonECContext += '}\n'
        ECContext += '}\n'
        return nonECContext, ECContext

    def addRepresentation(self, statement: Statement, nonECContext, ECContext):
        ECRepresentation = statement.getEventCalculusRepresentation()
        nonECRepresentation = statement.getFluents()
        for i in range(0, len(ECRepresentation)):
            ECRule = createChoiceRule(ECRepresentation[i])
            nonECRule = createChoiceRule(nonECRepresentation[i])
            if nonECContext[-1] != '{' and nonECContext[-1] != '\n':
                nonECContext += '.\n'
                ECContext += '.\n'
            nonECContext += nonECRule
            ECContext += ECRule
        return nonECContext, ECContext

    def addPredicates(self, predicates, context):
        for predicate in predicates:
            if context[-1] != '{':
                context += '.\n'
            context += predicate
        return context

    def createLearningFile(self):
        file = open(self.filename, 'w')
        # add in the background knowledge only if using the event calculus
        if self.corpus.isEventCalculusNeeded:
            for rule in self.corpus.backgroundKnowledge:
                file.write(rule)
                file.write('\n')
            for bias in self.corpus.ECModeBias:
                file.write(bias)
                file.write('\n')
            generalConstraints = self.generateGeneralConstraints(self.corpus.ECModeBias, self.corpus.constantModeBias)
        else:
            for bias in self.corpus.nonECModeBias:
                file.write(bias)
                file.write('\n')
            generalConstraints = self.generateGeneralConstraints(self.corpus.nonECModeBias,
                                                                 self.corpus.constantModeBias)

        # for constraint in generalConstraints:
        #    file.write(constraint)
        #    file.write('\n')

        for constantBias in self.corpus.constantModeBias:
            file.write(constantBias)
            file.write('\n')

        if self.corpus.isEventCalculusNeeded:
            file.write("#maxv(4)")
        else:
            file.write("#maxv(3)")
        file.write('.\n')

        file.write("#max_penalty(50).\n")

        if self.corpus.isEventCalculusNeeded:
            for example in self.corpus.eventCalculusExamples:
                file.write(example)
                file.write('\n')
        else:
            for example in self.corpus.nonEventCalculusExamples:
                file.write(example)
                file.write('\n')
        self.currentExamplesIndex = len(self.corpus.nonEventCalculusExamples)

    def appendExamplesToLearningFile(self):
        file = open(self.filename, 'a')
        for index in range(self.currentExamplesIndex, len(self.corpus.nonEventCalculusExamples)):
            if self.corpus.isEventCalculusNeeded:
                file.write(self.corpus.eventCalculusExamples[index])
            else:
                file.write(self.corpus.nonEventCalculusExamples[index])
            file.write('\n')
        self.currentExamplesIndex = len(self.corpus.nonEventCalculusExamples)
        file.close()

    def solveILASPTask(self):
        command = "ILASP -q -nc -ml=2 --version=2i --cache-path=" + self.cachingFile + " " + self.filename
        output = os.popen(command).read()
        return self.processILASP(output)

    def processILASP(self, output):
        lines = output.split('\n')
        return set([line for line in lines if line])

    def addExamples(self, NonECExample, ECExample):
        self.corpus.addNonECExample(NonECExample)
        self.corpus.addECExample(ECExample)

    def generateGeneralConstraints(self, modeBias, constantModeBias):
        constraints = set()
        for rule in modeBias:
            representation = getRepresentationFromModeBias(rule)
            if numberOfConstantArguments(representation) == 0 and numberOfNonConstantArguments(representation) >= 2:
                constraint = createConstraint(representation)
                constraints.add(createBias(constraint))
            # elif numberOfNonConstantArguments(representation) >= 2 and numberOfConstantArguments(representation) == 1:
            #    for constant in constantModeBias:
            #        if hasConstantType(constant, representation):
            #            substitutedRepresentation = substituteConstant(constant, representation)
            #            constraint = createConstraint(substitutedRepresentation)
            #            constraints.add(createBias(constraint))
        return constraints
