import re
from ReasoningModule.reasoner import getAnswer, createRegularExpression
from StoryStructure.Story import Story


# This code was used to investigate preferences in Task 16 of the bAbI dataset. These preferences are discussed in the
# Future Work chapter of the report
def findSpecificAnswer(answers, question, story: Story):
    if len(answers) == 1:
        return answers
    name = question.getFluents()[0][0].split('(')[1].split(',')[0]
    print("Name", name)
    animalPredicate = "be(" + name + ",V1)"
    print("Animal Predicate Finder:", animalPredicate)
    for sentence in story:
        pattern = createRegularExpression(animalPredicate)
        compiledPattern = re.compile(pattern)
        rule = sentence.getFluents()[0][0]
        result = compiledPattern.fullmatch(rule)
        if result:
            fullMatch = result[0]
    animal = fullMatch.split(',')[1][:-1]
    print("Animal:", animal)
    index = 0
    for sentence in story:
        if animal in sentence.text and name not in sentence.text.lower():
            index = story.getIndex(sentence)
    animalName = story.get(index).getFluents()[0][0].split('(')[1].split(',')[0]
    print("Name of previous animal:", animalName)
    colorPredicate = "be_color(" + animalName + ",V1)"
    print("Color predicate: ", colorPredicate)
    answer = None
    for sentence in story:
        pattern = createRegularExpression(colorPredicate)
        compiledPattern = re.compile(pattern)
        rule = sentence.getFluents()[0][0]
        result = compiledPattern.fullmatch(rule)
        if result:
            fullMatch = result[0]
            answer = getAnswer(fullMatch, colorPredicate)
    if answer in answers:
        return [answer]
    else:
        return answers
