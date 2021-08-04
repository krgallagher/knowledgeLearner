import speech_recognition
from StoryStructure.Corpus import Corpus
from StoryStructure.Story import Story
from gtts import gTTS
import os
import speech_recognition as sr

from TranslationalModule.InteractiveParser import InteractiveParser


class InteractiveSystem:
    def __init__(self, audio=False):
        self.audio = audio  # might want to rename this variable
        self.language = "en"  # putting this here to make the code slightly more flexible
        self.corpus = Corpus()
        self.currentStory = Story()
        self.parser = InteractiveParser()

        # get new input
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
                    self.corpus.append(self.currentStory)  # will have to check later that this works correctly.
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
            currentInput = self.getInput()

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

        # do an initial parsing of the sentence
        self.parser.parse(sentence)
        print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
              sentence.getFluents(), sentence.getPredicates(), sentence.getModeBiasFluents())


if __name__ == "__main__":
    system = InteractiveSystem()
# TODO: Implement a sort of timer.
# in order to deal with audio and microphone, might be able to have different functions for printing etc.


# --------------------------------------------------
# Ideas
# maybe if no punctuation is given then print a "sorry I didn't quite get that message"
