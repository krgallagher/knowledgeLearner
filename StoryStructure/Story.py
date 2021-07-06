class Story:
    def __init__(self):
        self.sentences = []

    def addSentence(self, sentence):
        self.sentences.append(sentence)

    def getSentences(self):
        return self.sentences