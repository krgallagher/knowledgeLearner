from StoryStructure.Corpus import Corpus
from StoryStructure.Statement import Statement
from StoryStructure.Question import Question
from StoryStructure.Story import Story


class bAbIReader:
    def __init__(self, filename):
        self.corpus = Corpus()
        file = open(filename, 'r')
        lines = file.readlines()
        story = Story()
        self.corpus.append(story)
        for line in lines:
            currentStatement = self.createStatement(line)
            if currentStatement.getLineID() == 1:
                newStory = Story()
                self.corpus.append(newStory)
            currentStory = self.corpus.pop()
            currentStory.addSentence(currentStatement)
            self.corpus.append(currentStory)

    def createStatement(self, line):
        index = line.index(" ") + 1
        identification = line[:index - 1]
        data = line[index:].split("\t")
        text = data[0].strip()
        if len(data) == 1:
            return Statement(identification, text)
        else:
            hints = data[2].split(" ")
            answer = data[1]
            return Question(identification, text, answer, hints)


if __name__ == "__main__":
    reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    for story1 in reader.corpus:
        sentences = story1.getSentences()
        for statement in sentences:
            print(statement.getLineID(), statement.getText())
