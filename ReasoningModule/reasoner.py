import os
import re
from StoryStructure.Question import Question
from Utilities.ILASPSyntax import createTimeRange


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


def whereSearch(question: Question, answerSet, eventCalculusRepresentationNeeded):
    # create a regular expression
    answers = []
    if eventCalculusRepresentationNeeded:
        representation = question.getEventCalculusRepresentation()
    else:
        representation = question.getFluents()
    pattern = createRegularExpression(representation)
    compiledPattern = re.compile(pattern)
    for rule in answerSet:
        result = compiledPattern.fullmatch(rule)
        if result:
            fullMatch = result[0]
            answers.append(getAnswer(fullMatch, representation))
    return answers


def isInAllAnswerSets(question: Question, answerSets):
    # create regular expression pattern to be matched
    eventCalculusRepresentation = question.getEventCalculusRepresentation()
    pattern = createRegularExpression(eventCalculusRepresentation)
    compiledPattern = re.compile(pattern)

    numAnswerSetsIn = 0
    for answerSet in answerSets:
        for rule in answerSet:
            result = compiledPattern.fullmatch(rule)
            if result:
                numAnswerSetsIn += 1
                break
    return numAnswerSetsIn == len(answerSets)


def searchForAnswer(question: Question, answerSets, eventCalculusRepresentationNeeded):
    if "where" in question.getText().lower() or "what" in question.getText().lower():
        answers = []
        for answerSet in answerSets:
            newAnswers = whereSearch(question, answerSet, eventCalculusRepresentationNeeded)
            answers += newAnswers
        if answers:
            return answers[0]
        return "unknown"
    elif "is" == question.getText()[0:2].lower():
        if isInAllAnswerSets(question, answerSets):
            return "yes"
        else:
            return "no"


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
    answerSets = processClingoOutput(output)
    return answerSets


class Reasoner:
    def __init__(self, corpus):
        self.corpus = corpus

    def computeAnswer(self, question, story, eventCalculusNeeded=True):
        # create Clingo file
        filename = self.createClingoFile(question, story, eventCalculusNeeded)

        file = open(filename, 'r')
        for line in file:
            print(line)


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
        if eventCalculusNeeded:
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
                    temp.write(statement.getEventCalculusRepresentation())
                    temp.write('.\n')
                else:
                    temp.write(statement.getFluents())
                    temp.write('.\n')

            # write the predicates even if the statement is a question
            for predicate in statement.getPredicates():
                temp.write(predicate)
                temp.write('.\n')
            if statement == question:
                break
        temp.write(createTimeRange(question))
        temp.close()
        return filename


if __name__ == '__main__':
    representation = "go(V1,bathroom)"
    print(createRegularExpression(representation))
