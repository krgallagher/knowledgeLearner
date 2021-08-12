import os
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.EventCalculus import initiatedAt, terminatedAt, holdsAt, happensAt
from TranslationalModule.ExpressivityChecker import createChoiceRule
from Utilities.ILASPSyntax import createTimeRange, modeHWrapping, modeBWrapping, varWrapping, addConstraints


# could generate the mode bias in one full swoop, might end up being better because then can always do caching.qu


class Learner:
    def __init__(self, corpus, filename="/Users/katiegallagher/Desktop/IndividualProject/learningFile.las",
                 cachingFile="/Users/katiegallagher/Desktop/IndividualProject/cachingFile.las", useSupervision=False):
        # will probably eventually want to make the default be in the tmp bin, but this is okay for now I think
        self.filename = filename
        self.cachingFile = cachingFile
        self.corpus = corpus
        self.oldModeBias = set()
        self.oldConstantBias = set()
        self.previousStoryIndexForIncorrectQuestion = 0  # default to the first story
        self.previousExampleAddedIndex = 0  # the last index that has been added for a positive/negative example
        self.useSupervision = useSupervision
        self.wasEventCalculusNeededPreviously = False
        self.currentExamplesIndex = 0

    # only learn something if the answer is incorrect. (Can always revert this change back)
    def learn(self, question: Question, story: Story, answer):
        if question.isWhereQuestion() or question.isWhatQuestion() or question.isWhoQuestion():
            if answer == ["nothing"] or not answer or question.isCorrectAnswer(answer):
                # might be able to get rid of the question.isCorrectAnswer, just think about the interactive system
                self.createPositiveExample(question, story)
            else:
                self.createNegativeExample(question, story, answer)
        else:
            if "yes" in question.getAnswer() or "maybe" in question.getAnswer():
                self.createPositiveExample(question, story)
            else:
                self.createNegativeExample(question, story)

        # store the old mode bias
        self.oldModeBias = self.corpus.modeBias.copy()
        self.oldConstantBias = self.corpus.constantModeBias.copy()

        # update the old mode bias.
        if self.wasEventCalculusNeededPreviously != self.corpus.isEventCalculusNeeded:
            self.corpus.modeBias = set()
            self.corpus.constantModeBias = set()
            self.addModeBias(story, question)
        else:
            self.updateModeBias(story, question)

        if self.oldModeBias == self.corpus.modeBias and self.oldConstantBias == self.corpus.constantModeBias:
            self.appendExamplesToLearningFile()
        else:
            if os.path.exists(self.cachingFile):
                os.remove(self.cachingFile)
            self.createLearningFile()

        # update the index of the previous story to have a question wrong.
        self.previousStoryIndexForIncorrectQuestion = self.corpus.getIndex(story)

        file = open(self.filename, 'r')
        for line in file:
            print(line)

        hypotheses = self.solveILASPTask()

        # refactor this
        unsatisfiable = set()
        unsatisfiable.add("UNSATISFIABLE")

        print("HYPOTHESES", hypotheses)
        if hypotheses != unsatisfiable:
            self.corpus.setHypotheses(hypotheses)

        self.wasEventCalculusNeededPreviously = self.corpus.isEventCalculusNeeded

        print("CURRENT HYPOTHESES: ", self.corpus.getHypotheses())

    # TODO uncomment this later on and remove the pass
    def __del__(self):
        # delete file from computer
        # os.remove(self.filename)
        pass

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

        # append all the extra event calculus and other predicates for the context aspect
        nonECContext, ECContext = self.createContext(question, story)
        negativeNonECExample = '#pos(' + positiveNonECPortion + ',' + negativeNonECPortion + ',' + nonECContext + ').'
        negativeECExample = '#pos(' + positiveECPortion + ',' + negativeECPortion + ',' + ECContext + ').'
        self.addExamples(negativeNonECExample, negativeECExample)

    # TO DO might want to redo the above so that it works better
    def createCautiousNegativeExample(self, question: Question, story: Story, answer=None):
        negativeNonECPortion, negativeECPortion = question.createPartialInterpretation(answer)
        nonECContext, ECContext = self.createContext(question, story)
        negativeNonECExample = '#neg(' + negativeNonECPortion + ',{},' + nonECContext + ').'
        negativeECExample = '#neg(' + negativeECPortion + ',{},' + ECContext + ').'
        self.addExamples(negativeNonECExample, negativeECExample)

    def createContext(self, question: Question, story: Story):
        predicates = set()
        nonECContext, ECContext = '{', '{'
        context = '{'
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

        # add in the mode bias
        for bias in self.corpus.modeBias:
            biasToAdd = bias
            # if not self.corpus.isEventCalculusNeeded:
            #    biasToAdd = addConstraints(bias)
            file.write(biasToAdd)
            file.write('\n')

        for constantBias in self.corpus.constantModeBias:
            file.write(constantBias)
            file.write('\n')

        # might want to make this so it starts with 4 variables and then gradually increases.
        if self.corpus.isEventCalculusNeeded:
            file.write("#maxv(4)")
        else:
            file.write("#maxv(3)")
        file.write('.\n')

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
        # command = "FastLAS --nopl" + filename
        command = "ILASP -q -nc --version=4 --cache-path=" + self.cachingFile + " " + self.filename
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
                self.addConstantModeBias(sentence)

        # add the mode bias for current story
        for index in range(0, story.getIndex(question) + 1):
            self.addStatementModeBias(story.get(index))
            self.addConstantModeBias(story.get(index))

    # new function that might need to change a bit
    def addModeBias(self, story: Story, question: Statement):
        for storyIndex in range(0, self.corpus.getIndex(story)):
            for sentence in self.corpus.stories[storyIndex]:
                self.addStatementModeBias(sentence)
                self.addConstantModeBias(sentence)

        for index in range(0, story.getIndex(question) + 1):
            self.addStatementModeBias(story.get(index))
            self.addConstantModeBias(story.get(index))

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

    def addConstantModeBias(self, sentence):
        for constantBias in sentence.constantModeBias:
            self.corpus.addConstantModeBias(constantBias)

    def addExamples(self, NonECExample, ECExample):

        self.corpus.addNonECExample(NonECExample)
        self.corpus.addECExample(ECExample)
