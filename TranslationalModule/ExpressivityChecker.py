import os
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Sentence
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from StoryStructure.Story import Story
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
    constraint += sentence.getEventCalculusRepresentation()[0][0]

    # will also need to change the way answers are stored here...
    for answer in sentence.getAnswer():
        constraint += ', ' + 'V1 != ' + answer
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
            # TODO change this into a boolean function
            if "yes" in sentence.getAnswer() or "no" in sentence.getAnswer() or "maybe" in sentence.getAnswer():
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
    for story in corpus:
        # create a clingo file that evaluates the expressivitiy of the corpus
        filename = createExpressivityClingoFile(story, corpus)

        #file = open(filename, 'r')
        #for line in file:
        #    print(line)

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
    trainingCorpus = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa8_lists-sets_train.txt")
    testingCorpus = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa8_lists-sets_test.txt")

    # initialise parser
    parser = BasicParser(trainingCorpus, testingCorpus)

    if isEventCalculusNeeded(trainingCorpus):
        print("EVENT CALCULUS IS NEEDED!")
    else:
        print("EVENT CALCULUS IS NOT NEEDED!")
