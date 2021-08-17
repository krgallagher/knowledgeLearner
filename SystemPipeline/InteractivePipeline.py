import sys

import speech_recognition
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from StoryStructure.Story import Story
from gtts import gTTS
import os
import speech_recognition as sr

from TranslationalModule.BasicParser import getSubstitutedText
from TranslationalModule.EventCalculus import wrap
from TranslationalModule.ExpressivityChecker import isEventCalculusNeeded
from TranslationalModule.InteractiveParser import InteractiveParser


# TODO think about when I am adding the story to the corpus

def convertListToString(answerToQuestion):
    stringAnswer = ""
    for index in range(0, len(answerToQuestion)):
        stringAnswer += answerToQuestion[index] + " "
        if index != len(answerToQuestion) - 1:
            stringAnswer += "and "
    return stringAnswer


class InteractiveSystem:
    def __init__(self, audio=False):
        self.audio = audio  # might want to rename this variable
        self.language = "en"  # putting this here to make the code slightly more flexible
        self.corpus = Corpus()
        self.currentStory = Story()
        self.parser = InteractiveParser(self.corpus)
        self.reasoner = Reasoner(self.corpus)
        self.learner = Learner(self.corpus)

        self.corpus.append(self.currentStory)

        currentInput = self.getInput(
            "Tell me a story, one sentence at a time, or type \'Help\' for more information!\n")
        print(currentInput)
        while currentInput:

            currentInput = currentInput.strip()

            if currentInput.lower() == "help":
                self.printHelpMenu()

            elif currentInput.lower() == "check hypotheses":
                print(self.corpus.getHypotheses())

            elif currentInput.lower() == "new story":
                if len(self.currentStory) > 0:
                    self.currentStory = Story()
                print("Tell me a new story.")

            elif currentInput.lower() == "end":
                break

            elif currentInput.lower() == "print story":
                print(self.currentStory)

            elif currentInput.lower() == "print corpus":
                print(self.corpus)

            else:
                self.processInput(currentInput)

            # get new input
            currentInput = self.getInput("Please continue your story.\n")

    def printHelpMenu(self):
        print("****************Help Menu****************")
        print("The following are special inputs for the system.")
        print("Type \"Help\" to display this menu.")
        print("Type \"End\" to end the program.")
        print("Type \"Check Hypotheses\" to display the current hypotheses for the corpus.")
        print("Type \"New Story\" to begin a new story.")
        print("Type \"Print Story\" to print the current story.")
        print("Type \"Print Corpus\" to print the current corpus.")

    def getInput(self, currentText=""):
        if self.audio:
            if currentText:
                self.output(currentText)

            r = sr.Recognizer()
            with sr.Microphone() as source:
                audio_text = r.listen(source)
                try:
                    audio = r.recognize_google(audio_text)
                    # print("Text: " + audio )
                except speech_recognition.UnknownValueError:
                    print("Sorry, I did not get that")  # make this speech
                    self.getInput()
                return audio
        else:
            return input(currentText)

    def output(self, currentText):
        if self.audio:
            myobj = gTTS(text=currentText, lang=self.language, slow=False)
            myobj.save("currentText.mp3")
            os.system("mpg321 currentText.mp3")
        else:
            print(currentText)

    def processInput(self, currentInput):

        # process the sentence
        sentence = self.parser.createStatement(currentInput, self.currentStory)
        print(sentence.getText(), sentence.getLineID())

        # do coreferencing here and have it be interactive.
        self.doCoreferencingAndSetDoc(sentence)

        # do an initial parsing of the sentence
        self.parser.parse(sentence)

        wrap(sentence)

        self.doSynonymSearchAndUpdate(sentence)

        print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
              sentence.getFluents(), sentence.getPredicates(), sentence.getModeBiasFluents())

        if isinstance(sentence, Question):
            answerToQuestion = self.reasoner.computeAnswer(sentence, self.currentStory)

            if answerToQuestion:
                currentInput = self.getInput(convertListToString(answerToQuestion) + "\nIs this correct?\n")
                if "y" in currentInput:
                    return
                currentInput = self.getInput("\nPlease tell me the answer: " + sentence.text + "\n")
            else:
                currentInput = self.getInput("I do not know. Please tell me.\n")

            sentence.setAnswer([currentInput])

            if not self.corpus.isEventCalculusNeeded and isEventCalculusNeeded(self.corpus):
                self.corpus.isEventCalculusNeeded = True

            self.parser.assembleModeBias()

            self.learner.learn(sentence, self.currentStory, answerToQuestion, createNewLearningFile=True)

    def doCoreferencingAndSetDoc(self, sentence):
        pronoun, possibleReferences = self.parser.coreferenceFinder(sentence, self.currentStory)
        if not pronoun:
            self.parser.setDocAndExtractProperNouns(sentence.text, sentence)
            return
        if possibleReferences:
            for i in range(0, len(possibleReferences)):
                phrase = "Does \"" + pronoun + "\" refer to " + possibleReferences[i] + "?\n"
                inputText = self.getInput(phrase)
                if "y" in inputText:
                    statementText = getSubstitutedText(pronoun, possibleReferences[i], sentence)
                    print(statementText)
                    self.parser.setDocAndExtractProperNouns(statementText, sentence)
                    return
        phrase = "Who does \"" + pronoun + "\" refer to?\n"
        inputText = self.getInput(phrase).lower()
        self.parser.setDocAndExtractProperNouns(getSubstitutedText(pronoun, inputText, sentence.text), sentence)

    def doSynonymSearchAndUpdate(self, sentence):
        fluentBase, potentialSynonyms = self.parser.checkSynonyms(sentence)
        if not potentialSynonyms:
            return
        for i in range(0, len(potentialSynonyms)):
            phrase = "By \"" + fluentBase + "\", do you mean \"" + potentialSynonyms[i] + "\"?\n"
            inputText = self.getInput(phrase)
            if "y" in inputText:
                self.parser.updateSynonymDictionary(fluentBase, potentialSynonyms[i])


def printSystemHelpMenu():
    print("Usage: InteractivePipeline.py [options]\n")
    print("General Options: ")
    print("\t --dialogueMethod=[spoken|written]")


if __name__ == "__main__":
    interactive = False
    if len(sys.argv) != 2:
        printSystemHelpMenu()
    elif sys.argv[1] == "--dialogueMethod=spoken":
        system = InteractiveSystem(audio=True)
    elif sys.argv[1] == "--dialogueMethod=written":
        system = InteractiveSystem(audio=False)
    else:
        printSystemHelpMenu()

# TODO: Implement a sort of timer.
# in order to deal with audio and microphone, might be able to have different functions for printing etc.
