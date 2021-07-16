import os
import re
from StoryStructure.Question import Question


# TODO assumes to left-hand parentheses and two right-hand parentheses, easy to adjust this code
def createRegularExpression(eventCalculusRepresentation):
    # split with left hand parentheses
    leftSplit = eventCalculusRepresentation.split('(')
    rightSplit = leftSplit[2].split(')')
    arguments = rightSplit[0].split(',')
    regularExpression = leftSplit[0] + '\(' + leftSplit[1] + '\('
    for index in range(0, len(arguments)):
        if "V" in arguments[index]:
            arguments[index] = ".+"
    for argument in arguments:
        if regularExpression[-1] != '(':
            regularExpression += ','
        regularExpression += argument
    regularExpression += '\)' + rightSplit[1] + '\)'
    return regularExpression


def getAnswer(fullMatch, eventCalculusRepresentation):
    leftSplitEC = eventCalculusRepresentation.split('(')
    rightSplitEC = leftSplitEC[2].split(')')
    argumentsEC = rightSplitEC[0].split(',')
    leftSplitMatch = fullMatch.split('(')
    rightSplitMatch = leftSplitMatch[2].split(')')
    argumentsMatch = rightSplitMatch[0].split(',')
    for index in range(0, len(argumentsEC)):
        if argumentsEC[index] != argumentsMatch[index]:
            answer = argumentsMatch[index]
            return answer
    return None


def whereSearch(question, answerSet):
    # create a regular expression
    answers = []
    eventCalculusRepresentation = question.getEventCalculusRepresentation()
    pattern = createRegularExpression(eventCalculusRepresentation)
    compiledPattern = re.compile(pattern)
    for rule in answerSet:
        result = compiledPattern.fullmatch(rule)
        if result:
            fullMatch = result[0]
            answers.append(getAnswer(fullMatch, eventCalculusRepresentation))
    return answers


def isInAllAnswerSets(question, answerSets):
    #create regular expression pattern to be matched
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

def searchForAnswer(question, answerSets):
    if "where" in question.getText().lower():
        answers = []
        for answerSet in answerSets:
            newAnswers = whereSearch(question, answerSet)
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

    def computeAnswer(self, question, story):
        # create Clingo file
        filename = self.createClingoFile(question, story)

        # use clingo to gather the answer sets from the file (if there are any)
        answerSets = getAnswerSets(filename)

        # parse the answer sets accordingly to give an answer
        answer = searchForAnswer(question, answerSets)

        # delete the file
        os.remove(filename)

        return answer

    def createClingoFile(self, question, story):
        filename = '/tmp/ClingoFile.las'
        temp = open(filename, 'w')

        # add in the background knowledge
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
                temp.write(statement.getEventCalculusRepresentation())
                temp.write('.\n')
            # write the predicates even if the statement is a question
            for predicate in statement.getPredicates():
                temp.write(predicate)
                temp.write('.\n')
            if statement == question:
                break
        temp.close()
        return filename


if __name__ == '__main__':
    predicate1 = "holdsAt(go(mary,V1),1)"
    predicate2 = "holedsAt(go(mary,bathroom),1)"
    print(getAnswer(predicate2, predicate1))

