import os
import re
from num2words import num2words
from StoryStructure.Question import Question
from StoryStructure.Story import Story
from TranslationalModule.ExpressivityChecker import createChoiceRule
from Utilities.ILASPSyntax import createTimeRange

'''
def findSpecificAnswer(answers, question, story: Story):
    if len(answers) == 1:
        return answers
    name = question.getFluents()[0][0].split('(')[1].split(',')[0]
    print("Name", name)
    animalPredicate = "be(" + name + ",V1)"
    print("Animal Predicate Finder:", animalPredicate)
    for sentence in story:
        pattern = createRegularExpression(animalPredicate)
        compiledPattern = re.compile(pattern)
        rule = sentence.getFluents()[0][0]
        result = compiledPattern.fullmatch(rule)
        if result:
            fullMatch = result[0]
    animal = fullMatch.split(',')[1][:-1]
    print("Animal:", animal)
    index = 0
    for sentence in story:
        if animal in sentence.text and name not in sentence.text.lower():
            index = story.getIndex(sentence)
    animalName = story.get(index).getFluents()[0][0].split('(')[1].split(',')[0]
    print("Name of previous animal:", animalName)
    colorPredicate = "be_color(" + animalName + ",V1)"
    print("Color predicate: ", colorPredicate)
    answer = None
    for sentence in story:
        pattern = createRegularExpression(colorPredicate)
        compiledPattern = re.compile(pattern)
        rule = sentence.getFluents()[0][0]
        result = compiledPattern.fullmatch(rule)
        if result:
            fullMatch = result[0]
            answer = getAnswer(fullMatch, colorPredicate)
    if answer in answers:
        return [answer]
    else:
        return answers
    #check if the animal is in a sentences text, and get the index of the last one
'''


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


class Reasoner:
    def __init__(self, corpus, filename='/tmp/ClingoFile.las'):
        self.filename = filename
        self.corpus = corpus

    def computeAnswer(self, question: Question, story):
        # create Clingo file
        self.createClingoFile(question, story)

        # file = open(self.filename, 'r')
        # for line in file:
        #    print(line)

        answerSets = self.getAnswerSets()

        answer = self.searchForAnswer(question, answerSets)

        # delete the file
        os.remove(self.filename)

        return answer

    def getAnswerSets(self):
        command = "Clingo -W none -n 0 " + self.filename
        output = os.popen(command).read()
        return processClingoOutput(output)

    def createClingoFile(self, question: Question, story: Story):
        file = open(self.filename, 'w')

        # add in the background knowledge
        if self.corpus.isEventCalculusNeeded:
            for rule in self.corpus.backgroundKnowledge:
                file.write(rule)
                file.write('\n')

        # add in the hypotheses
        for hypothesis in self.corpus.hypotheses:
            file.write(hypothesis)
            file.write('\n')

        # add in the statements from the story
        for statement in story:
            if not isinstance(statement, Question):
                if self.corpus.isEventCalculusNeeded:
                    representation = statement.getEventCalculusRepresentation()
                else:
                    representation = statement.getFluents()
                for i in range(0, len(representation)):
                    choiceRule = createChoiceRule(representation[i])
                    file.write(choiceRule)
                    file.write('.\n')

            # write the predicates even if the statement is a question
            for predicate in statement.getPredicates():
                file.write(predicate)
                file.write('.\n')
            if statement == question:
                break
        file.write(createTimeRange(question.getLineID()))
        file.write('.\n')
        file.close()

    def searchForAnswer(self, question: Question, answerSets):
        if question.isWhereQuestion() or question.isWhatQuestion() or question.isWhoQuestion():
            answers = []
            for answerSet in answerSets:
                newAnswers = self.whereSearch(question, answerSet)
                answers += newAnswers
            if answers:
                return answers
            if question.isWhatQuestion():
                return ["nothing"]
            else:
                return []
        elif question.isYesNoMaybeQuestion():
            return self.isPossibleAnswer(question, answerSets)
        elif question.isHowManyQuestion():
            answers = []
            for answerSet in answerSets:
                newAnswers = self.whereSearch(question, answerSet)
                answers += newAnswers
            if answers:
                return [num2words(len(answers))]
            return ["none"]
        return []

    # TODO rename this since this funciton is used for more than a "where" search
    def whereSearch(self, question: Question, answerSet):
        # create a regular expression
        answers = []
        if self.corpus.isEventCalculusNeeded:
            representation = question.getEventCalculusRepresentation()[0][0]
        else:
            representation = question.getFluents()[0][0]
        pattern = createRegularExpression(representation)
        compiledPattern = re.compile(pattern)
        for rule in answerSet:
            result = compiledPattern.fullmatch(rule)
            if result:
                fullMatch = result[0]
                answers.append(getAnswer(fullMatch, representation))
        return answers

    # TODO edit this to have both the event calculus and non-event calculus representation taken into account
    def isPossibleAnswer(self, question: Question, answerSets):
        # create regular expression pattern to be matched
        if self.corpus.isEventCalculusNeeded:
            representation = question.getEventCalculusRepresentation()[0][0]
        else:
            representation = question.getFluents()[0][0]
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
