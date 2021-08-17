import os
from StoryStructure import Statement
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from StoryStructure.Story import Story
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
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


def createYesNoRule(question: Question):
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


def createExpressivityClingoFile(story: Story, corpus: Corpus):
    filename = '/tmp/ClingoFile.lp'
    temp = open(filename, 'w')

    # add in the background knowledge
    for rule in corpus.backgroundKnowledge:
        temp.write(rule)
        temp.write('\n')
    for sentence in story:
        representation = sentence.getEventCalculusRepresentation()
        if isinstance(sentence, Question):
            if sentence.answer:
                if sentence.isYesNoMaybeQuestion():
                    rule = createYesNoRule(sentence)
                    temp.write(rule)
                    temp.write('.\n')
                else:
                    questionWithAnswers = sentence.getQuestionWithAnswers()
                    for predicate in questionWithAnswers:
                        temp.write(predicate)
                        temp.write('.\n')
                    expressivityConstraint = createExpressivityConstraint(sentence, questionWithAnswers)
                    temp.write(expressivityConstraint)
                    temp.write('.\n')

        else:
            for i in range(0, len(representation)):
                choiceRule = createChoiceRule(representation[i])
                temp.write(choiceRule)
                temp.write('.\n')

    temp.write(createTimeRange(len(story)))
    temp.write('.\n')
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
