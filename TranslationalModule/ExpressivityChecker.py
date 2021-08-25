import os
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Statement
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from StoryStructure.Story import Story
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.DatasetParser import DatasetParser
from Utilities.ILASPSyntax import createTimeRange


def createExpressivityConstraint(sentence: Question):
    questionWithAnswers = sentence.getQuestionWithAnswers()
    constraint = ":- "
    for predicate in questionWithAnswers:
        if questionWithAnswers.index(predicate) != 0:
            constraint += ', '
        constraint += predicate
    constraint += ', '
    constraint += sentence.getEventCalculusRepresentation()[0][0]
    for answer in sentence.getAnswer():
        constraint += ', ' + 'V1 != ' + answer.lower()
    return constraint


def createYesNoMaybeRule(question: Question):
    if "yes" in question.getAnswer():
        return ":- not " + question.getEventCalculusRepresentation()[0][0]
    if "no" in question.getAnswer():
        return ":- " + question.getEventCalculusRepresentation()[0][0]
    else:
        return question.getEventCalculusRepresentation()[0][0]


def createChoiceRule(fluents, statement, eventCalculusUsage=False):
    if len(fluents) == 1:
        if statement.negatedVerb and not eventCalculusUsage:
            return ":- " + fluents[0]
        return fluents[0]
    rule = "1{"
    for fluent in fluents:
        if rule[-1] != "{":
            rule += ";"
        rule += fluent
    rule += "}1"
    return rule


def createExpressivityFile(story: Story, corpus: Corpus, filename='/tmp/ILASPExpressivityFile.las'):
    file = open(filename, 'w')
    for rule in corpus.backgroundKnowledge:
        file.write(rule)
        file.write('\n')
    inclusionOrExclusion = []
    context = []
    for sentence in story:
        representation = sentence.getEventCalculusRepresentation()
        if isinstance(sentence, Question):
            if sentence.isYesNoMaybeQuestion():
                rule = createYesNoMaybeRule(sentence)
                if "yes" in sentence.getAnswer() or "no" in sentence.getAnswer():
                    context.append(rule)
                else:
                    inclusionOrExclusion.append(rule)
            else:
                questionWithAnswers = sentence.getQuestionWithAnswers()
                for predicate in questionWithAnswers:
                    context.append(predicate)
                expressivityConstraint = createExpressivityConstraint(sentence)
                context.append(expressivityConstraint)
        else:
            for i in range(0, len(representation)):
                choiceRule = createChoiceRule(representation[i], sentence, eventCalculusUsage=True)
                context.append(choiceRule)
    context.append(createTimeRange(len(story)))
    if not inclusionOrExclusion:
        file.write(createPositiveExample([], [], context))
        return filename
    for element in inclusionOrExclusion:
        file.write(createPositiveExample([element], [], context))
        file.write(createPositiveExample([], [element], context))
    return filename


def createPositiveExample(inclusionList, exclusionList, contextList):
    inclusion = ""
    for element in inclusionList:
        if inclusion:
            inclusion += ","
        inclusion += element
    exclusion = ""
    for element in exclusionList:
        if exclusion:
            exclusion += ","
        exclusion += element
    context = ""
    for element in contextList:
        if context:
            context += ".\n"
        context += element
    if context:
        context += ".\n"
    return "#pos({" + inclusion + "},{" + exclusion + "},{" + context + "}).\n"


def isUnsatisfiable(output):
    return "UNSATISFIABLE" in output


def runILASP(filename):
    command = "ILASP --version=4 " + filename
    output = os.popen(command).read()
    return output


def isEventCalculusNeeded(corpus: Corpus):
    semanticNetwork = ConceptNetIntegration()
    for story in corpus:
        for sentence in story:
            for rule in sentence.constantModeBias:
                if semanticNetwork.hasTemporalAspect(rule.split(',')[1].split(')')[0]):
                    return False
    for story in corpus:
        filename = createExpressivityFile(story, corpus)
        answerSets = runILASP(filename)
        if isUnsatisfiable(answerSets):
            os.remove(filename)
            return True
        os.remove(filename)
    return False


if __name__ == "__main__":
    trainingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task10_train"
    testingSet = "/Users/katiegallagher/Desktop/smallerVersionOfTask/task10_test"
    trainCorpus = bAbIReader(trainingSet)
    testCorpus = bAbIReader(testingSet)
    DatasetParser(trainCorpus, testCorpus, useSupervision=False)
    print(isEventCalculusNeeded(trainCorpus))
