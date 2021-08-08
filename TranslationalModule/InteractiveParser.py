from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from StoryStructure.Story import Story
from TranslationalModule.BasicParser import BasicParser


def instanceOfQuestion(text):
    if "?" in text:  # might want to make this more elaborate but probably fine for right now
        return True
    return False


class InteractiveParser(BasicParser):
    def __init__(self):
        super().__init__()

    def createStatement(self, text, story: Story):
        text = text.strip()
        lineID = len(story) + 1
        if instanceOfQuestion(text):
            sentence = Question(lineID, text)
        else:
            sentence = Statement(lineID, text)
        # will set the doc in the coreferencing part of the pipeline

        # sentence.doc = self.nlp(text)
        story.addSentence(sentence)
        return sentence

    def setDoc(self, text, sentence: Statement):
        sentence.doc = self.nlp(text)

