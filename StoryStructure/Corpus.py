from DatasetReader.BackgroundKnowledge import eventCalculusAxioms


class Corpus:
    def __init__(self):
        self.stories = []
        # note that the background knowledge is a set
        self.backgroundKnowledge = eventCalculusAxioms()  # might want to eventually set this up differently to make it more general, but fine for now
        self.modeBias = set()
        self.hypotheses = set()  # might want to change this to a set?
        # might want to add a variable for the hypothesis space

    def append(self, story):
        self.stories.append(story)

    def __iter__(self):
        ''' Returns the Iterator object '''
        return CorpusIterator(self)

    def pop(self):
        return self.stories.pop()

    def setHypotheses(self, newHypotheses):
        self.hypotheses = newHypotheses

    def getHypotheses(self):
        return self.hypotheses

    def updateModeBias(self, modeBias):
        self.modeBias.update(modeBias)


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


if __name__ == "__main__":
    corpus = Corpus()
    corpus.append("cat")
    corpus.append("dog")
    corpus.append("fish")
    for animal in corpus:
        print(animal)
    print(corpus.backgroundKnowledge)
