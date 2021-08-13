from DatasetReader.BackgroundKnowledge import eventCalculusAxioms
import random

from StoryStructure.Question import Question
from StoryStructure.Story import Story

class Corpus:
    def __init__(self):
        self.constantModeBias = set()
        self.stories = []
        self.backgroundKnowledge = eventCalculusAxioms()
        self.modeBias = set()
        self.hypotheses = set()
        self.isEventCalculusNeeded = False
        self.choiceRulesPresent = False
        self.nonEventCalculusExamples = []
        self.eventCalculusExamples = []
        # store examples in both representations?

    def append(self, story):
        self.stories.append(story)

    def addNonECExample(self, example):
        self.nonEventCalculusExamples.append(example)

    def addECExample(self, example):
        self.eventCalculusExamples.append(example)

    def reset(self):
        self.modeBias = set()
        self.hypotheses = set()
        self.isEventCalculusNeeded = False
        self.choiceRulesPresent = False
        self.nonEventCalculusExamples = []

    def __iter__(self):
        ''' Returns the Iterator object '''
        return CorpusIterator(self)

    def pop(self):
        return self.stories.pop()

    def setHypotheses(self, newHypotheses):
        self.hypotheses = newHypotheses

    def addHypotheses(self, newHypotheses):
        self.hypotheses.update(newHypotheses)

    def addBackgroundKnowledge(self, additionalBackgroundKnowledge):
        self.backgroundKnowledge.update(additionalBackgroundKnowledge)

    def removeMostRecentHypotheses(self):
        self.hypotheses.pop()

    def getHypotheses(self):
        return self.hypotheses

    def updateModeBias(self, modeBias):
        self.modeBias.update(modeBias)

    def addConstantModeBias(self, constantBias):
        self.constantModeBias.add(constantBias)

    def shuffle(self):
        random.seed(4)
        random.shuffle(self.stories)

    def getIndex(self, story: Story):
        return self.stories.index(story)

    def get(self, index):
        return self.stories[index]

    def __str__(self):
        sentenceRepresentation = ""
        for story in self.stories:
            sentenceRepresentation += str(story) + "\n\n"
        return sentenceRepresentation


class CorpusIterator:
    ''' Iterator class '''

    def __init__(self, corpus):
        # Corpus object reference
        self._corpus = corpus
        # member variable to keep track of current index
        self._index = 0

    def __next__(self):
        if self._index < len(self._corpus.stories):
            result = self._corpus.stories[self._index]
            self._index += 1
            return result
        # End of Iteration
        raise StopIteration


def pruneCorpus(corpus: Corpus, numExamples):
    newCorpus = Corpus()
    numQuestions = 0
    for story in corpus:
        currentStory = Story()
        newCorpus.append(currentStory)
        for sentence in story:
            if numQuestions >= numExamples:
                return newCorpus
            currentStory.addSentence(sentence)
            if isinstance(sentence, Question):
                numQuestions += 1



if __name__ == "__main__":
    corpus = Corpus()
    corpus.append("cat")
    corpus.append("dog")
    corpus.append("fish")
    for animal in corpus:
        print(animal)
    print(corpus.backgroundKnowledge)
