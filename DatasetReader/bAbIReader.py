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
    reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa19_path-finding_train.txt")
    for story1 in reader.corpus:
        sentences = story1.getSentences()
        for statement in sentences:
            print(statement.getLineID(), statement.getText())
            if isinstance(statement, Question):
                print(statement.getAnswer(), statement.getHints())
