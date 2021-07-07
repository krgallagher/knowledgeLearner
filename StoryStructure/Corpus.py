from StoryStructure import Story


class Corpus:
    def __init__(self):
        self.stories = []
        # might want to add a variable for the hypothesis space

    def append(self, story):
        self.stories.append(story)

    def __iter__(self):
        ''' Returns the Iterator object '''
        return CorpusIterator(self)


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