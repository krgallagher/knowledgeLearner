import os

from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Statement
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from StoryStructure.Story import Story
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.DatasetParser import DatasetParser
from Utilities.ILASPSyntax import createTimeRange


def createExpressivityConstraint(sentence: Statement, questionWithAnswers):
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
        return question.getEventCalculusRepresentation()[0][0]
    else:
        return ":- " + question.getEventCalculusRepresentation()[0][0]


def createChoiceRule(fluents):
    if len(fluents) == 1:
        return fluents[0]
    rule = "1{"
    for fluent in fluents:
        if rule[-1] != "{":
            rule += ";"
        rule += fluent
    rule += "}1"
    return rule


def createExpressivityClingoFile(story: Story, corpus: Corpus, filename='/tmp/ClingoFile.lp' ):
    file = open(filename, 'w')

    for rule in corpus.backgroundKnowledge:
        file.write(rule)
        file.write('\n')
    for sentence in story:
        representation = sentence.getEventCalculusRepresentation()
        if isinstance(sentence, Question):
            if sentence.answer:
                if sentence.isYesNoMaybeQuestion():
                    rule = createYesNoMaybeRule(sentence)
                    file.write(rule)
                    file.write('.\n')
                else:
                    questionWithAnswers = sentence.getQuestionWithAnswers()
                    for predicate in questionWithAnswers:
                        file.write(predicate)
                        file.write('.\n')
                    expressivityConstraint = createExpressivityConstraint(sentence, questionWithAnswers)
                    file.write(expressivityConstraint)
                    file.write('.\n')

        else:
            for i in range(0, len(representation)):
                choiceRule = createChoiceRule(representation[i])
                file.write(choiceRule)
                file.write('.\n')

    file.write(createTimeRange(len(story)))
    file.write('.\n')
    return filename


def isUnsatisfiable(output):
    return "UNSATISFIABLE" in output


def runClingo(filename):
    command = "Clingo -W none -n 0 " + filename
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
        filename = createExpressivityClingoFile(story, corpus)

        answerSets = runClingo(filename)

        if isUnsatisfiable(answerSets):
            os.remove(filename)
            return True

        os.remove(filename)
    return False


if __name__ == "__main__":
    trainingSet = "../en/qa" + "16" + "_train.txt"
    testingSet = "../en/qa" + "16" + "_test.txt"
    train = bAbIReader(trainingSet)
    test = bAbIReader(testingSet)
    DatasetParser(train, test)
    print(isEventCalculusNeeded(train))
