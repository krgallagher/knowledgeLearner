import os

from pyswip import Prolog

from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from TranslationalModule.bAbIParser import bAbIParser


class Reasoner:
    def __init__(self, corpus):
        self.corpus = corpus

    def computeAnswer(self, question, story):
        filename = self.createLearningFile(question, story)

        # use clingo to gather the answer sets from the file (if there are any)
        answerSets = self.getAnswerSets(filename)

        # parse the answer sets accordingly to give an answer
        answer = self.searchForAnswer(question, answerSets)
        # delete the file
        os.remove(filename)

        return answer

    def createLearningFile(self, question, story):
        filename = '/tmp/learningFile.las'
        temp = open(filename, 'w')
        # add in the background knowledge
        for rule in self.corpus.backgroundKnowledge:
            temp.write(rule)
            temp.write('\n')
        # add in the hypotheses
        for hypothesis in self.corpus.hypotheses:
            temp.write(hypothesis)
            temp.write('\n')
        # for statement in story
        for statement in story.getSentences():
            if not isinstance(statement, Question):
                temp.write(statement.getEventCalculusRepresentation())
                temp.write('\n')
            for predicate in statement.getPredicates():
                temp.write(predicate)
                temp.write('\n')
            if statement == question:
                break
        temp.close()
        return filename

    def deleteFile(self, filename):
        os.remove(filename)

    def getAnswerSets(self, filename):
        command = "Clingo -W none -n 0 " + filename
        output = os.popen(command).read()
        answerSets = self.processClingoOutput(output)
        return answerSets

    def processClingoOutput(self, output):
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

    def searchForAnswer(self, question, answerSets):
        if "where" in question.getText().lower():
            answers = []
            for answerSet in answerSets:
                newAnswers = self.whereSearch(question, answerSet)
                answers += newAnswers
            if answers:
                return answers[0]
            return "UNKNOWN"

    def whereSearch(self, question, answerSet):
        prolog = Prolog()
        for rule in answerSet:
            prolog.assertz(rule)
        queryPredicate = question.getEventCalculusRepresentation().strip('.')
        prolog.assertz(self.replaceTimeStamp(queryPredicate))
        solution = list(prolog.query(queryPredicate.strip('.')))
        return solution

    def replaceTimeStamp(self, queryPredicate):
        tmp = queryPredicate.split(')')
        newPredicate = tmp[0] + '),-1)'
        return newPredicate


if __name__ == '__main__':
    # process data
    reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task1_train")

    # initialise parser
    parser = bAbIParser(reader.corpus)
    reasoner = Reasoner(reader.corpus)
    for story in reader.corpus:
        statements = story.getSentences()
        for statement in statements:
            parser.parse(statements, statement)
            if isinstance(statement, Question):
                answer = reasoner.computeAnswer(statement, story)
                print(answer)
            # filename = reasoner.createLearningFile(statement, story)
            # reader = open(filename, 'r')
            # for line in reader:
            #    print(line)
            # print(reasoner.getAnswerSets(filename))
            # os.remove(filename)

# need a function which takes in a corpus and evaluates accordingly
# takes in a corpus plus the current story, i.e. the "context"


# the reasoner should take in a question and output an answer

# at all times, the reasoner needs the corpus, since it needs the background knowledge and hypotheses
