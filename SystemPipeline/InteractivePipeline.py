import sys
import speech_recognition
from LearningModule.learner import Learner
from LearningModule.modeBiasGenerator import ModeBiasGenerator
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


def convertListToString(answerToQuestion):
    stringAnswer = ""
    for index in range(0, len(answerToQuestion)):
        stringAnswer += answerToQuestion[index] + " "
        if index != len(answerToQuestion) - 1:
            stringAnswer += "and "
    return stringAnswer


class InteractivePipeline:
    def __init__(self, audio=False, audioFilePath='/tmp/audioFilePath.mp3'):
        self.audio = audio
        self.language = "en"
        self.corpus = Corpus()
        self.currentStory = Story()
        self.parser = InteractiveParser(self.corpus)
        self.reasoner = Reasoner(self.corpus)
        self.learner = Learner(self.corpus)
        self.modeBiasGenerator = ModeBiasGenerator(self.corpus)
        self.corpus.append(self.currentStory)
        self.audioFilePath = audioFilePath

        if self.audio:
            moreInformation = 'say'
        else:
            moreInformation = 'type'
        currentInput = self.getInput(
            "Tell me a story, one sentence at a time, or " + moreInformation + "  \'Help\'' for more information!\n")
        while currentInput:

            currentInput = currentInput.strip()

            if currentInput.lower() == "help":
                self.outputHelpMenu()

            elif currentInput.lower() == "check hypotheses":
                hypotheses = self.corpus.getHypotheses()
                if hypotheses:
                    if self.audio:
                        hypotheses = self.formatHypothesesForAudio()
                    self.output(hypotheses)
                else:
                    self.output("There are no current hypotheses.")

            elif currentInput.lower() == "new story":
                if len(self.currentStory) > 0:
                    self.currentStory = Story()
                self.output("Tell me a new story.")

            elif currentInput.lower() == "end":
                break

            elif currentInput.lower() == "print story":
                story = str(self.currentStory)
                self.output(story)

            elif currentInput.lower() == "print corpus":
                corpus = str(self.corpus)
                self.output(corpus)

            else:
                self.processInput(currentInput)

            currentInput = self.getInput("Please continue your story.\n")

    def __del__(self):
        if os.path.exists(self.audioFilePath):
            os.remove(self.audioFilePath)

    def outputHelpMenu(self):
        if self.audio:
            method = "Say "
        else:
            print("****************Help Menu****************")
            method = "Type "
        self.output(
            "The following are special inputs for the system.\n"
            + method + "\"Help\" to display this menu.\n"
            + method + "\"End\" to end the program.\n"
            + method + "\"Check Hypotheses\" to display the current hypotheses for the corpus.\n"
            + method + "\"New Story\" to begin a new story.\n"
            + method + "\"Print Story\" to print the current story.\n"
            + method + "\"Print Corpus\" to print the current corpus.")

    def getInput(self, currentText=""):
        if self.audio:
            if currentText:
                self.output(currentText)
            r = sr.Recognizer()
            with sr.Microphone() as source:
                audio_text = r.listen(source)
                try:
                    audio = r.recognize_google(audio_text)
                    print("Text: " + audio)
                except speech_recognition.UnknownValueError:
                    audio = self.getInput("Sorry, I did not get that!")
                return audio
        else:
            return input(currentText)

    def output(self, currentText):
        if self.audio:
            myobj = gTTS(text=currentText, lang=self.language, slow=False)
            myobj.save(self.audioFilePath)
            os.system("mpg321 -q " + self.audioFilePath + ">/dev/null 2>&1")
        else:
            print(currentText)

    def processInput(self, currentInput):
        sentence = self.parser.createStatement(currentInput, self.currentStory)


        self.doCoreferencingAndSetDoc(sentence)

        self.parser.parse(sentence)

        wrap(sentence)

        self.doSynonymSearchAndUpdate(sentence)

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

            self.corpus.ECModeBias = set()
            self.corpus.nonECModeBias = set()
            self.modeBiasGenerator.assembleModeBias()

            self.learner.learn(sentence, self.currentStory, answerToQuestion, createNewLearningFile=True)

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
                    statementText = getSubstitutedText(pronoun, possibleReferences[i], sentence)
                    # print(statementText)
                    self.parser.setDoc(statementText, sentence)
                    return
        phrase = "Who does \"" + pronoun + "\" refer to?\n"
        inputText = self.getInput(phrase).lower()
        self.parser.setDoc(getSubstitutedText(pronoun, inputText, sentence.text), sentence)

    def doSynonymSearchAndUpdate(self, sentence):
        fluentBase, potentialSynonyms = self.parser.checkSynonyms(sentence)
        if not potentialSynonyms:
            return
        for i in range(0, len(potentialSynonyms)):
            phrase = "By \"" + fluentBase + "\", do you mean \"" + potentialSynonyms[i] + "\"?\n"
            inputText = self.getInput(phrase)
            if "y" in inputText:
                self.parser.updateSynonymDictionary(fluentBase, potentialSynonyms[i])

    def formatHypothesesForAudio(self):
        hypotheses = list(self.corpus.getHypotheses())
        formattedHypotheses = ""
        print(self.corpus.getHypotheses())
        for i in range(0, len(hypotheses)):
            formattedHypotheses += "Hypothesis number " + str(i)
            hypothesis = hypotheses[i].split(':-')
            print(hypothesis)



def printSystemHelpMenu():
    print("Usage: InteractivePipeline.py [options]\n")
    print("General Options: ")
    print("\t -dialogueMethod=[spoken|written]")


if __name__ == "__main__":
    interactive = False
    if len(sys.argv) != 2:
        printSystemHelpMenu()
    elif sys.argv[1] == "-dialogueMethod=spoken":
        system = InteractivePipeline(audio=True)
    elif sys.argv[1] == "-dialogueMethod=written":
        system = InteractivePipeline(audio=False)
    else:
        printSystemHelpMenu()
