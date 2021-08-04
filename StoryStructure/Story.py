from StoryStructure import Statement


class Story:
    def __init__(self):
        self.sentences = []
        self.examples = []  # list of positive and negative examples

    def reset(self):
        self.examples = set()

    def __len__(self):
        return len(self.sentences)

    def addSentence(self, sentence):
        self.sentences.append(sentence)

    def getSentences(self):
        return self.sentences

    def getIndex(self, sentence: Statement):
        return self.sentences.index(sentence)

    def get(self, index):
        return self.sentences[index]

    def getExamples(self):
        return self.examples

    def getExample(self, index):
        return self.examples[index]

    def size(self):
        return len(self.sentences)

    # the story class does not need to worry about how to create a positive/negative example,
    # it only needs to worry about how to store it
    def appendExample(self, example):
        self.examples.append(example)

    def __iter__(self):
        ''' Returns the Iterator object '''
        return StoryIterator(self)

    def __str__(self):
        sentenceRepresentation = ""
        for sentence in self.sentences:
            sentenceRepresentation += str(sentence) + " "
        return sentenceRepresentation


# iterator class
class StoryIterator:
    ''' Iterator class '''

    def __init__(self, story):
        # story object reference
        self._story = story
        # member variable to keep track of current index
        self._index = 0

    def __next__(self):
        if self._index < len(self._story.sentences):
            result = self._story.sentences[self._index]
            self._index += 1
            return result
        # End of Iteration
        raise StopIteration
