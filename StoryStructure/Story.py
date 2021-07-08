class Story:
    def __init__(self):
        self.sentences = []
        self.examples = set()  # set of positive and negative examples

    def addSentence(self, sentence):
        self.sentences.append(sentence)

    def getSentences(self):
        return self.sentences

    # the story class does not need to worry about how to create a positive/negative example,
    # it only needs to worry about how to store it
    def appendExample(self, example):
        self.examples.add(example)
