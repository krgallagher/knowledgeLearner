import spacy
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Story
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import wrap


def varWrapping(tag):
    return "var(" + tag + ")"


def hasADPChild(noun, doc):
    return [token for token in doc if token.head == noun and token.pos_ == "ADP"]


def isDisjunctive(noun, doc):
    conjunctives = [token.text.lower() for token in doc if token.head == noun and token.pos_ == "CCONJ"]
    return "or" in conjunctives


class BasicParser:
    def __init__(self, trainCorpus, testCorpus):
        self.nlp = spacy.load("en_core_web_lg")  # should use large for best parsing
        self.synonymDictionary = {}
        self.conceptNet = ConceptNetIntegration()
        self.conceptsToExplore = set()
        self.trainCorpus = trainCorpus
        self.testCorpus = testCorpus

        # parse the training set
        for story in self.trainCorpus:
            for sentence in story:
                self.parse(story, sentence)

        # parse the testing set
        for story in self.testCorpus:
            for sentence in story:
                self.parse(story, sentence)
        # play around with the synonym dictionary
        self.synonymDictionary.update(self.conceptNet.synonymFinder(self.conceptsToExplore))
        self.updateFluents()
        self.setEventCalculusRepresentation()
        print(self.synonymDictionary)

    def coreferenceFinder(self, statement: Statement, story: Story):
        statementText = statement.getText()
        index = story.getIndex(statement)
        if index == 0:
            return statementText
        previousIndex = index - 1
        currentSentence = self.nlp(statementText)
        previousSentence = self.nlp(story.get(previousIndex).getText())
        pronoun = [token for token in currentSentence if token.pos_ == "PRON"]
        properNoun = [token for token in previousSentence if token.pos_ == "PROPN"]
        if properNoun:
            replacementPhrase = properNoun[0].text
            if properNoun[0].conjuncts:  # might want to generalise for or conjuncts as well
                for noun in properNoun[0].conjuncts:
                    replacementPhrase += " and " + noun.text
            return statementText.replace(" " + pronoun[0].text + " ", " " + replacementPhrase + " ")
        return statementText

    def parse(self, story: Story, statement: Statement):
        doc = self.nlp(statement.getText())

        # check for coreferences
        pronouns = [token for token in doc if token.pos_ == "PRON"]
        if pronouns:
            doc = self.nlp(self.coreferenceFinder(statement, story))

        # check for negations
        negation = [token for token in doc if token.dep_ == 'neg' and token.tag_ == 'RB']
        if negation:
            statement.negatedVerb = True

        # creating the fluent base
        fluentBase = self.createFluentBase(doc)

        # if the statement is not a question, then add concepts to explore
        # if not isinstance(statement, Question):
        conceptsToExplore = set()
        if fluentBase.split('_')[0] != 'be' and not isinstance(statement, Question):
            conceptsToExplore.add(fluentBase)
            self.conceptsToExplore.update(conceptsToExplore)

        # now we need to form a statement/question fluent
        nouns = [token for token in doc if "NN" in token.tag_ and token.text.lower() not in fluentBase.split('_')]
        fluent = fluentBase + "("
        fluents = [[fluent]]
        modeBiasFluents = [[fluent]]
        nounsCopy = nouns.copy()
        for noun in nouns:
            if noun in nounsCopy:
                disjunctive = isDisjunctive(noun, doc)
                conjuncts = [noun] + list(noun.conjuncts)
                newFluents = []
                newMBFluents = []
                for conjunct in conjuncts:
                    nounsCopy.remove(conjunct)
                if disjunctive:
                    for i in range(0, len(fluents)):
                        orFluentList = []
                        orMBFluentList = []
                        for conjunct in conjuncts:
                            for j in range(0, len(fluents[i])):
                                newFluent, newMBFluent = self.addNounToFluent(statement, conjunct, fluents[i][j],
                                                                              modeBiasFluents[i][j], nounsCopy)
                                orFluentList.append(newFluent)
                                orMBFluentList.append(newMBFluent)
                        newFluents.append(orFluentList)
                        newMBFluents.append(orMBFluentList)
                else:
                    for i in range(0, len(fluents)):
                        for conjunct in conjuncts:
                            fluents1 = []
                            mbfluents1 = []
                            for j in range(0, len(fluents[i])):
                                resultingFluent, resultingMBFluent = self.addNounToFluent(statement, conjunct,
                                                                                          fluents[i][j],
                                                                                          modeBiasFluents[i][j],
                                                                                          nounsCopy)
                                fluents1.append(resultingFluent)
                                mbfluents1.append(resultingMBFluent)
                            newFluents.append(fluents1)
                            newMBFluents.append(mbfluents1)
                fluents = newFluents
                modeBiasFluents = newMBFluents

        if isinstance(statement, Question):
            if "where" in statement.getText().lower() or "what" in statement.getText().lower():
                for i in range(0, len(fluents)):
                    for j in range(0, len(fluents[i])):
                        if not fluents[i][j][-1] == '(':
                            fluents[i][j] += ','
                            modeBiasFluents[i][j] += ','
                        fluents[i][j] += "V1"
                        modeBiasFluents[i][j] += varWrapping('nn')

        for i in range(0, len(fluents)):
            for j in range(0, len(fluents[i])):
                fluents[i][j] += ")"
                modeBiasFluents[i][j] += ")"
        statement.setFluents(fluents)
        statement.setModeBiasFluents(modeBiasFluents)
        return

    def createFluentBase(self, doc):
        # print(statement.getText())
        fluentBase = ""

        # get root verb or something similar to it...
        root = [token for token in doc if token.head == token][0]
        childVerb = [child for child in root.children if child.pos_ == 'VERB']
        if childVerb:
            root = childVerb[0]
        fluentBase += root.lemma_
        # print("Fluent Base:", fluentBase)

        # add modifiers, maybe include comaprators here?
        verb_modifier = [token for token in doc if token.tag_ == 'JJR' or token.dep_ == "acomp"]
        if verb_modifier:
            fluentBase += '_' + verb_modifier[0].lemma_
        # print("Verb modifiers: ", verb_modifier)
        # add adpositions
        adposition = [token for token in doc if
                      token.pos_ == "ADP" and (token.head == root or token.head.pos_ == "ADV")]
        # print("Adpositions", adposition)
        if adposition:
            # nouns = [token for token in doc if
            #        token.head == adposition[0] and token.tag_ == 'NN' and hasADPChild(token, doc)]
            # print("Adposition 0 nouns:", nouns)
            # if nouns:
            #    fluentBase += '_' + nouns[0].text.lower()
            fluentBase += '_' + adposition[0].text.lower()
        return fluentBase

    def addNounToFluent(self, statement: Statement, noun, fluent, modeBiasFluent, nouns):
        # might be able to have a loop here, something like, for choice in fluent.
        tag = noun.tag_.lower()
        # ignore plural
        if tag == 'nns':
            tag = 'nn'
        # TODO append ADP children to the noun in some way and remove a noun while doing it

        children = [child for child in noun.children]
        descriptiveNoun = ""
        for child in children:
            if child.pos_ == "ADJ":
                if descriptiveNoun:
                    descriptiveNoun += "_"
                descriptiveNoun += child.text.lower()
        if descriptiveNoun:
            descriptiveNoun += "_"
        descriptiveNoun += noun.lemma_.lower()
        for child in children:
            relevantNouns = [aChild for aChild in child.children if "NN" in aChild.tag_]
            if child.pos_ == "ADP" and nouns:
                descriptiveNoun += "_" + child.text.lower() + "_" + relevantNouns[0].text.lower()
                nouns.remove(nouns[0])

        if fluent[-1] != '(':
            fluent += ','
            modeBiasFluent += ','
        fluent += descriptiveNoun
        modeBiasFluent += varWrapping(tag)
        # add tag predicates
        relevantPredicate = tag + '(' + descriptiveNoun + ')'
        statement.addPredicate(relevantPredicate)
        return fluent, modeBiasFluent

    def updateFluents(self):
        for story in self.trainCorpus:
            for sentence in story:
                fluents, modeBiasFluents = sentence.getFluents(), sentence.getModeBiasFluents()
                sentence.setFluents(self.update(fluents))
                sentence.setModeBiasFluents(self.update(modeBiasFluents))
        for story in self.testCorpus:
            for sentence in story:
                fluents, modeBiasFluents = sentence.getFluents(), sentence.getModeBiasFluents()
                sentence.setFluents(self.update(fluents))
                sentence.setModeBiasFluents(self.update(modeBiasFluents))

    def update(self, fluents):
        newFluents = []
        for i in range(0, len(fluents)):
            currentFluents = []
            for j in range(0, len(fluents[i])):
                splitFluent = fluents[i][j].split('(')
                predicate = splitFluent[0]
                if predicate in self.synonymDictionary.keys():
                    updatedFluent = self.synonymDictionary[predicate]
                else:
                    updatedFluent = predicate
                for index in range(1, len(splitFluent)):
                    updatedFluent += '(' + splitFluent[index]
                currentFluents.append(updatedFluent)
            newFluents.append(currentFluents)
        return newFluents

    def setEventCalculusRepresentation(self):
        for story in self.trainCorpus:
            for sentence in story:
                wrap(sentence)
        for story in self.testCorpus:
            for sentence in story:
                wrap(sentence)


if __name__ == '__main__':
    # process data
    # reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    trainCorpus = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task2_train")
    testCorpus = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task2_test")

    # initialise parser
    parser = BasicParser(trainCorpus, testCorpus)

    for story in trainCorpus:
        for sentence in story:
            print(sentence.getText(), sentence.getLineID(), sentence.getFluents(),
                  sentence.getEventCalculusRepresentation(), sentence.getPredicates(), sentence.getModeBiasFluents())
            if isinstance(sentence, Question):
                print(sentence.getModeBiasFluents())
    print(trainCorpus.modeBias)
    print(parser.synonymDictionary)
