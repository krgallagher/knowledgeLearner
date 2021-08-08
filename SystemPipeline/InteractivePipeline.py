import speech_recognition
from LearningModule.learner import Learner
from ReasoningModule.reasoner import Reasoner
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from StoryStructure.Story import Story
from gtts import gTTS
import os
import speech_recognition as sr
from TranslationalModule.EventCalculus import wrap
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
        self.parser = InteractiveParser()
        self.reasoner = Reasoner(self.corpus)
        self.learner = Learner(self.corpus)

        # append the first story
        self.corpus.append(self.currentStory)

        # set the event calculus needed
        self.corpus.isEventCalculusNeeded = True

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

        # search for synonyms -- will likely need to create a new component for this since it is interactive

        # update fluents

        # set event calculus representation
        wrap(sentence)

        print(sentence.getText(), sentence.getEventCalculusRepresentation(), sentence.getLineID(),
              sentence.getFluents(), sentence.getPredicates(), sentence.getModeBiasFluents())

        # if it is a question, then use the reasoner
        if isinstance(sentence, Question):
            # if the event calculus is so far not needed, then do an expressivity checker here.

            answerToQuestion = self.reasoner.computeAnswer(sentence, self.currentStory)

            if answerToQuestion:
                currentInput = self.getInput(convertListToString(answerToQuestion) + "\nIs this correct?\n")
                if "y" in currentInput:
                    return
                currentInput = self.getInput("\nPlease tell me the answer: " + sentence.text + "\n")
            else:
                currentInput = self.getInput("I do not know. Please tell me.\n")

            sentence.setAnswer([currentInput])
            self.learner.learn(sentence, self.currentStory, answerToQuestion)

    def doCoreferencingAndSetDoc(self, sentence):
        pronoun, possibleReferences = self.parser.coreferenceFinder(sentence, self.currentStory)
        if not pronoun:
            self.parser.setDoc(sentence.text, sentence)
            return
        if possibleReferences:
            for i in range(0, len(possibleReferences)):
                phrase = "Does \"" + pronoun + "\" refer to " + possibleReferences[i] + "?\n"
                inputText = self.getInput(phrase)
                if "y" in inputText:
                    statementText = sentence.text.replace(pronoun + " ", possibleReferences[i] + " ")
                    print(statementText)
                    self.parser.setDoc(statementText, sentence)
                    return
        phrase = "Who does \"" + pronoun + "\" refer to?\n"
        inputText = self.getInput(phrase).lower()
        statementText = sentence.text.replace(" " + pronoun + " ", " " + inputText + " ")
        self.parser.setDoc(statementText, sentence)


if __name__ == "__main__":
    system = InteractiveSystem(False)
# TODO: Implement a sort of timer.
# in order to deal with audio and microphone, might be able to have different functions for printing etc.


# --------------------------------------------------
# Ideas

# assume that the event calculus is needed? Not sure how to deal with this here.
# maybe if no punctuation is given then print a "sorry I didn't quite get that message"
