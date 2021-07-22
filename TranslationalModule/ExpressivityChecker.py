import os
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Sentence
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from TranslationalModule.basicParser import BasicParser
from Utilities.ILASPSyntax import createTimeRange


# TODO change the way we work with yes/no questions for the expressivity constraints etc.
def createExpressivityConstraint(sentence: Sentence, questionWithAnswers):
    constraint = ":- "
    for predicate in questionWithAnswers:
        if questionWithAnswers.index(predicate) != 0:
            constraint += ', '
        constraint += predicate
    constraint += ', '
    constraint += sentence.getEventCalculusRepresentation().copy().pop()

    # will also need to change the way answers are stored here...
    for answer in sentence.getAnswer():
        constraint += ', ' + 'V1 != ' + answer
    return constraint


def createYesNoRule(question: Question):
    if "yes" in question.getAnswer():
        return question.getEventCalculusRepresentation().copy().pop()
    else:
        return ":- " + question.getEventCalculusRepresentation().copy().pop()


def createExpressivityClingoFile(story, corpus):
    filename = '/tmp/ClingoFile.lp'
    temp = open(filename, 'w')

    # add in the background knowledge
    for rule in corpus.backgroundKnowledge:
        temp.write(rule)
        temp.write('\n')

    for sentence in story:
        representation = sentence.getEventCalculusRepresentation()
        if isinstance(sentence, Question):
            if "yes" in sentence.getAnswer() or "no" in sentence.getAnswer():
                rule = createYesNoRule(sentence)
                temp.write(rule)
                temp.write('.\n')
                pass
            else:
                questionWithAnswers = sentence.getQuestionWithAnswers()
                for predicate in questionWithAnswers:
                    temp.write(predicate)
                    temp.write('.\n')
                expressivityConstraint = createExpressivityConstraint(sentence, questionWithAnswers)
                temp.write(expressivityConstraint)
                temp.write('.\n')
        else:
            for predicate in representation:
                temp.write(predicate)
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
    for story in corpus:
        # create a clingo file that evaluates the expressivitiy of the corpus
        filename = createExpressivityClingoFile(story, corpus)

        # run the file with clingo
        answerSets = runClingo(filename)

        # if it returns unsatisfiable then return True
        if isUnsatisfiable(answerSets):
            os.remove(filename)
            return True

    os.remove(filename)
    return False


if __name__ == "__main__":
    # process the data
    reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa9_simple-negation_train.txt")
    # get corpus
    corpus = reader.corpus

    # initialise parser
    parser = BasicParser(corpus)

    for story in corpus:
        for sentence in story:
            parser.parse(story, sentence)
    if isEventCalculusNeeded(corpus):
        print("EVENT CALCULUS IS NEEDED!")
    else:
        print("EVENT CALCULUS IS NOT NEEDED!")
