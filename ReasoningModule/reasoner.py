import os
import re
from StoryStructure.Question import Question
from TranslationalModule.ExpressivityChecker import createChoiceRule
from Utilities.ILASPSyntax import createTimeRange
from num2words import num2words


def createRegularExpression(representation):
    # split with left hand parentheses
    leftSplit = representation.split('(')
    rightSplit = leftSplit[len(leftSplit) - 1].split(')')
    arguments = rightSplit[0].split(',')
    regularExpression = ""
    for index in range(0, len(leftSplit) - 1):
        regularExpression += leftSplit[index] + '\('
    for index in range(0, len(arguments)):
        if "V" in arguments[index]:
            arguments[index] = ".+"
    for argument in arguments:
        if regularExpression[-1] != '(':
            regularExpression += ','
        regularExpression += argument
    regularExpression += '\)'
    for index in range(1, len(rightSplit) - 1):
        regularExpression += rightSplit[index] + '\)'
    return regularExpression


# TODO make this more malleable.
def getAnswer(fullMatch, representation):
    leftSplitRep = representation.split('(')
    rightSplitRep = leftSplitRep[len(leftSplitRep) - 1].split(')')
    argumentsRep = rightSplitRep[0].split(',')
    leftSplitMatch = fullMatch.split('(')
    rightSplitMatch = leftSplitMatch[len(leftSplitMatch) - 1].split(')')
    argumentsMatch = rightSplitMatch[0].split(',')
    for index in range(0, len(argumentsRep)):
        if argumentsRep[index] != argumentsMatch[index]:
            answer = argumentsMatch[index]
            return answer
    return None


def getTimeFromEventCalculusFluent(answer):
    return int(answer.split(',')[-1].split(')')[0])


def sortAccordingToTimeStamp(answers):
    print(answers)
    sorting = sorted(answers, key=answers.get)
    print(sorting)
    return sorted(answers, key=answers.get)


# TODO rename this since this funciton is used for more than a "where" search
def whereSearch(question: Question, answerSet, eventCalculusRepresentationNeeded):
    # create a regular expression
    answers = {}
    if eventCalculusRepresentationNeeded:
        representation = question.getEventCalculusRepresentation()[0][0]
    else:
        representation = question.getFluents()[0][0]
    representation = representation
    pattern = createRegularExpression(representation)
    compiledPattern = re.compile(pattern)
    for rule in answerSet:
        result = compiledPattern.fullmatch(rule)
        if result:
            fullMatch = result[0]
            if eventCalculusRepresentationNeeded:
                answers[getAnswer(fullMatch, representation)] = getTimeFromEventCalculusFluent(fullMatch)
            else:
                answers[getAnswer(fullMatch, representation)] = 0

    return sortAccordingToTimeStamp(answers)



# TODO edit this to have both the event calculus and non-event calculus representation taken into account
def isPossibleAnswer(question: Question, answerSets, eventCalculusRepresentationNeeded):
    # create regular expression pattern to be matched
    if eventCalculusRepresentationNeeded:
        representation = question.getEventCalculusRepresentation()[0][0]
    else:
        representation = question.getFluents()[0][0]
    representation = representation
    pattern = createRegularExpression(representation)
    compiledPattern = re.compile(pattern)
    numAnswerSetsIn = 0
    for answerSet in answerSets:
        for rule in answerSet:
            result = compiledPattern.fullmatch(rule)
            if result:
                numAnswerSetsIn += 1
                break
    if numAnswerSetsIn == len(answerSets):
        return ["yes"]
    elif numAnswerSetsIn >= 1:
        return ["maybe"]
    else:
        return ["no"]


def searchForAnswer(question: Question, answerSets, eventCalculusRepresentationNeeded):
    if question.isWhereQuestion() or question.isWhatQuestion():
        answers = []
        for answerSet in answerSets:
            newAnswers = whereSearch(question, answerSet, eventCalculusRepresentationNeeded)
            answers += newAnswers
        if answers:
            return answers
        return ["nothing"]
    elif question.isYesNoMaybeQuestion():
        return isPossibleAnswer(question, answerSets, eventCalculusRepresentationNeeded)
    elif question.isHowManyQuestion():
        answers = []
        for answerSet in answerSets:
            newAnswers = whereSearch(question, answerSet, eventCalculusRepresentationNeeded)
            answers += newAnswers
        if answers:
            return [num2words(len(answers))]
        return ["none"]
    return []


def processClingoOutput(output):
    answerSets = []
    data = output.split('\n')
    index = 0
    while index < len(data):
        if data[index] == "SATISFIABLE" or data[index] == "UNSATISFIABLE":
            break
        if "Answer" in data[index]:
            index += 1
            answerSet = set(data[index].split())
            answerSets.append(answerSet)
        index += 1
    return answerSets


def getAnswerSets(filename):
    command = "Clingo -W none -n 0 " + filename
    output = os.popen(command).read()
    return processClingoOutput(output)


class Reasoner:
    def __init__(self, corpus):
        self.corpus = corpus

    def computeAnswer(self, question, story, eventCalculusNeeded=True):
        # create Clingo file
        filename = self.createClingoFile(question, story, eventCalculusNeeded)

        # file = open(filename, 'r')
        # for line in file:
        #    print(line)

        # use clingo to gather the answer sets from the file (if there are any)
        answerSets = getAnswerSets(filename)

        # parse the answer sets accordingly to give an answer
        answer = searchForAnswer(question, answerSets, eventCalculusNeeded)

        # delete the file
        os.remove(filename)

        return answer

    def createClingoFile(self, question, story, eventCalculusNeeded):
        filename = '/tmp/ClingoFile.las'
        temp = open(filename, 'w')

        # add in the background knowledge
        # if eventCalculusNeeded:
        for rule in self.corpus.backgroundKnowledge:
            temp.write(rule)
            temp.write('\n')

        # add in the hypotheses
        for hypothesis in self.corpus.hypotheses:
            temp.write(hypothesis)
            temp.write('\n')

        # add in the statements from the story
        for statement in story:
            if not isinstance(statement, Question):
                if eventCalculusNeeded:
                    representation = statement.getEventCalculusRepresentation()
                else:
                    representation = statement.getFluents()
                for i in range(0, len(representation)):
                    choiceRule = createChoiceRule(representation[i])
                    temp.write(choiceRule)
                    temp.write('.\n')

            # write the predicates even if the statement is a question
            for predicate in statement.getPredicates():
                temp.write(predicate)
                temp.write('.\n')
            if statement == question:
                break
        temp.write(createTimeRange(question.getLineID()))
        temp.write('.\n')
        temp.close()
        return filename


if __name__ == "__main__":
    answers = ["holdsAt(carry(mary,football),5)"]
    print(sortAccordingToTimeStamp(answers))
