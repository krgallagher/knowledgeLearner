from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.BasicParser import BasicParser
from TranslationalModule.EventCalculus import wrap


def instanceOfQuestion(text):
    if "?" in text:
        return True
    return False


class InteractiveParser(BasicParser):
    def __init__(self, corpus):
        super().__init__()
        self.corpus = corpus

    def createStatement(self, text, story: Story):
        text = text.strip()
        lineID = len(story) + 1
        if instanceOfQuestion(text):
            sentence = Question(lineID, text)
        else:
            sentence = Statement(lineID, text)
        story.addSentence(sentence)
        return sentence

    def setDoc(self, text, sentence: Statement):
        sentence.doc = self.nlp(text)

    def checkSynonyms(self, sentence):
        fluentBase = sentence.getFluentBase()

        if fluentBase in self.synonymDictionary.keys():
            fluents, modeBiasFluents = sentence.getFluents(), sentence.getModeBiasFluents()
            sentence.setFluents(self.updateFluentAndMBFluent(fluents))
            sentence.setModeBiasFluents(self.updateFluentAndMBFluent(modeBiasFluents))
            return []
        if fluentBase in self.synonymDictionary.values():
            self.synonymDictionary[fluentBase] = fluentBase
            return []
        potentialSynonyms = []

        for key in self.synonymDictionary.keys():
            if self.conceptNet.isSynonym(fluentBase, key):
                potentialSynonyms.append(key)

        for concept in self.conceptsToExplore:
            if concept != fluentBase and self.conceptNet.isSynonym(fluentBase, concept):
                potentialSynonyms.append(concept)

        return fluentBase, potentialSynonyms

    def updateSynonymDictionary(self, fluentBase, newSynonym):
        self.synonymDictionary[fluentBase] = newSynonym
        self.synonymDictionary[newSynonym] = newSynonym
        for story in self.corpus:
            for sentence in story:
                self.updateSentence(sentence)
                wrap(sentence)


