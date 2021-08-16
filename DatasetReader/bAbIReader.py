from StoryStructure.Corpus import Corpus
from StoryStructure.Statement import Statement
from StoryStructure.Question import Question
from StoryStructure.Story import Story

def bAbIReader(filename):
    corpus = Corpus()
    file = open(filename, 'r')
    lines = file.readlines()
    story = Story()
    corpus.append(story)
    firstStory = True
    for line in lines:
        currentStatement = createStatement(line)
        if currentStatement.getLineID() == 1:
            if firstStory:
                firstStory = False
            else:
                newStory = Story()
                corpus.append(newStory)
        currentStory = corpus.pop()
        currentStory.addSentence(currentStatement)
        corpus.append(currentStory)
    return corpus


def createStatement(line):
    index = line.index(" ") + 1
    identification = line[:index - 1]
    data = line[index:].split("\t")
    text = data[0].strip()
    if len(data) == 1:
        return Statement(identification, text)
    else:
        hints = data[2].strip('\n').split(" ")  # might be able to disregard this hints eventually
        answer = data[1].split(',')
        return Question(identification, text, answer, hints)


if __name__ == "__main__":
    minSentences = -1
    maxSentences = -1
    minQuestions = -1
    maxQuestions = -1
    for i in range(1, 21):
        train = "../en/qa" + str(i) + "_train.txt"
        corpus1 = bAbIReader(train)
        print("Task: ", i)
        for story1 in corpus1:
            numSentences = 0
            numQuestions = 0
            sentences = story1.getSentences()
            for statement in sentences:
                numSentences += 1
               #print(statement.getLineID(), statement.getText())
                if isinstance(statement, Question):
                    numQuestions += 1
                    #print(statement.getAnswer(), statement.getHints())
            if minSentences == -1 or numSentences < minSentences:
                minSentences = numSentences
            if minQuestions == -1 or numQuestions < minQuestions:
                minQuestions = numQuestions
            if maxSentences == -1 or numSentences > maxSentences:
                maxSentences = numSentences
            if maxQuestions == -1 or numQuestions > maxQuestions:
                maxQuestions = numQuestions
            print("Number of Sentences: ", numSentences)
            print("Number of Questions: ", numQuestions)
    print("MAX SENTENCES: ", maxSentences)
    print("MIN SENTENCES: ", minSentences)
    print("MAX QUESTIONS: ", maxQuestions)
    print("MIN QUESTIONS: ", minQuestions)
