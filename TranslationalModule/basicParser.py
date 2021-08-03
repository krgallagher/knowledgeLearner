import spacy
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Story
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import wrap


# maybe go through at the beginning and grab 'similar terms' and try to parse

def varWrapping(tag):
    return "var(" + tag + ")"


def hasADPChild(noun, doc):
    return [token for token in doc if token.head == noun and token.pos_ == "ADP"]


def isDisjunctive(noun, doc):
    conjunctives = [token.text.lower() for token in doc if token.head == noun and token.pos_ == "CCONJ"]
    return "or" in conjunctives


def hasDetChild(token, sentence: Statement):
    if isinstance(sentence, Question) and not sentence.isYesNoMaybeQuestion():
        for child in token.children:
            if child.pos_ == "DET":
                return True
    return False


class BasicParser:
    def __init__(self, trainCorpus, testCorpus):
        self.nlp = spacy.load("en_core_web_lg")  # should use large for best parsing
        self.synonymDictionary = {}
        self.conceptNet = ConceptNetIntegration()
        self.conceptsToExplore = set()
        self.trainCorpus = trainCorpus
        self.testCorpus = testCorpus
        # self.modifiers = set()
        # self.determiners = set()

        # Set the doc for the training and testing corpus
        for story in self.trainCorpus:
            for sentence in story:
                sentence.doc = self.nlp(self.coreferenceFinder(sentence, story))
        for story in self.testCorpus:
            for sentence in story:
                sentence.doc = self.nlp(self.coreferenceFinder(sentence, story))
        # -------------------------------------------------
        '''
        for story in self.trainCorpus:
            for sentence in story:
                modifiers = self.getModifiers(sentence)
                determiners = self.getDeterminers(sentence)
                self.modifiers.update(modifiers)
                self.determiners.update(determiners)
        for story in self.testCorpus:
            for sentence in story:
                modifiers = self.getModifiers(sentence)
                self.modifiers.update(modifiers)
                determiners = self.getDeterminers(sentence)
                self.modifiers.update(modifiers)
                self.determiners.update(determiners)
        print(self.determiners)
        exit(150)
        '''
        # -------------------------------------------------

        # parse the training set
        for story in self.trainCorpus:
            for sentence in story:
                self.parse(sentence)

        # parse the testing set
        for story in self.testCorpus:
            for sentence in story:
                self.parse(sentence)
        # play around with the synonym dictionary
        self.synonymDictionary.update(self.conceptNet.synonymFinder(self.conceptsToExplore))
        # to be removed at a later point
        if "drop" in self.synonymDictionary.keys():
            self.synonymDictionary["leave"] = self.synonymDictionary["drop"]
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
        if pronoun and properNoun:
            replacementPhrase = properNoun[0].text
            if properNoun[0].conjuncts:  # might want to generalise for or conjuncts as well
                for noun in properNoun[0].conjuncts:
                    replacementPhrase += " and " + noun.text
            return statementText.replace(" " + pronoun[0].text + " ", " " + replacementPhrase + " ")
        return statementText

    def parse(self, statement: Statement):
        doc = statement.doc
        usedTokens = []

        # check for negations
        negation = [token for token in doc if token.dep_ == 'neg' and token.tag_ == 'RB']
        if negation:
            statement.negatedVerb = True

        # get the nouns of the sentence
        nouns = [token for token in doc if "NN" in token.tag_]

        nounsAndAdjectiveComplements = [token for token in doc if "NN" in token.tag_ or "JJ" in token.tag_]
        # and token.text.lower() not in fluentBase.split('_')

        # creating the fluent base
        fluentBase = self.createFluentBase(usedTokens, nouns, statement)

        # find the concepts to explore
        conceptsToExplore = set()
        if fluentBase.split('_')[0] != 'be' and not isinstance(statement, Question):
            conceptsToExplore.add(fluentBase)
            self.conceptsToExplore.update(conceptsToExplore)

        fluent = fluentBase + "("
        fluents = [[fluent]]
        modeBiasFluents = [[fluent]]

        if isinstance(statement, Question):
            if statement.isWhereQuestion() or statement.isWhatQuestion() or statement.isHowManyQuestion():
                nounSubject = [token for token in doc if token.dep_ == "nsubj"]
                if nounSubject and nounSubject[0].tag_ == "WP":
                    self.addVariable(fluents, modeBiasFluents)
                    fluents, modeBiasFluents = self.createMainPortionOfFluent(fluents, modeBiasFluents,
                                                                              nounsAndAdjectiveComplements,
                                                                              statement, usedTokens)
                else:
                    fluents, modeBiasFluents = self.createMainPortionOfFluent(fluents, modeBiasFluents,
                                                                              nounsAndAdjectiveComplements,
                                                                              statement, usedTokens)
                    self.addVariable(fluents, modeBiasFluents)
            else:
                fluents, modeBiasFluents = self.createMainPortionOfFluent(fluents, modeBiasFluents,
                                                                          nounsAndAdjectiveComplements,
                                                                          statement, usedTokens)
        else:
            fluents, modeBiasFluents = self.createMainPortionOfFluent(fluents, modeBiasFluents,
                                                                      nounsAndAdjectiveComplements, statement,
                                                                      usedTokens)

        for i in range(0, len(fluents)):
            for j in range(0, len(fluents[i])):
                fluents[i][j] += ")"
                modeBiasFluents[i][j] += ")"
        statement.setFluents(fluents)
        statement.setModeBiasFluents(modeBiasFluents)
        return

    def createMainPortionOfFluent(self, fluents, modeBiasFluents, nouns, statement, usedTokens):
        nounsCopy = nouns.copy()
        for noun in nouns:
            whDeterminer = [token for token in noun.children if token.tag_ == "WDT"]
            if whDeterminer:
                usedTokens.append(noun)
            if noun in nounsCopy and noun not in usedTokens:
                #print(statement.text, nounsCopy)
                disjunctive = isDisjunctive(noun, statement.doc)
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
                                                                              modeBiasFluents[i][j], nounsCopy, nouns)
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
                                                                                          nounsCopy, nouns)
                                fluents1.append(resultingFluent)
                                mbfluents1.append(resultingMBFluent)
                            newFluents.append(fluents1)
                            newMBFluents.append(mbfluents1)
                fluents = newFluents
                modeBiasFluents = newMBFluents
        return fluents, modeBiasFluents

    def addVariable(self, fluents, modeBiasFluents):
        for i in range(0, len(fluents)):
            for j in range(0, len(fluents[i])):
                if not fluents[i][j][-1] == '(':
                    fluents[i][j] += ','
                    modeBiasFluents[i][j] += ','
                fluents[i][j] += "V1"
                modeBiasFluents[i][j] += varWrapping('nn')

    def createFluentBase(self, usedTokens, nouns, sentence: Statement):
        fluentBase = ""

        # get root verb or something similar to it...
        root = [token for token in sentence.doc if token.head == token][0]
        childVerb = [child for child in root.children if child.pos_ == 'VERB']
        if childVerb:
            root = childVerb[0]
        fluentBase += root.lemma_
        usedTokens.append(root)

        typeDeterminer = [token.lemma_ for token in sentence.doc if hasDetChild(token, sentence)]
        if typeDeterminer:
            fluentBase = typeDeterminer[0]
            return fluentBase

        verb_modifier = [token for token in sentence.doc if token.tag_ == 'JJR' or token.dep_ == "acomp"]

        adposition = [token for token in sentence.doc if
                      token.pos_ == "ADP" and (token.head == root or len(nouns) <= 2)]

        # TODO recent addition: only add if the length is greater than or equal to 2.
        if verb_modifier and (len(nouns) >= 2 or isinstance(sentence, Question)):
            fluentBase += '_' + verb_modifier[0].lemma_
            ADPModifierChildren = [token for token in sentence.doc if
                                   token.pos_ == "ADP" and token.head == verb_modifier[0]]
            if ADPModifierChildren:
                fluentBase += '_' + ADPModifierChildren[0].lemma_
                usedTokens.append(ADPModifierChildren[0])
            usedTokens.append(verb_modifier[0])
        # print("Verb modifiers: ", verb_modifier)
        # add adpositions

        # print("Adpositions", adposition)
        if adposition and adposition[-1] not in usedTokens:
            fluentBase += '_' + adposition[-1].text.lower()
            usedTokens.append(adposition[-1])
        return fluentBase

    def addNounToFluent(self, statement: Statement, noun, fluent, modeBiasFluent, nouns, allNouns):
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
            if child.pos_ == "ADP" and nouns and len(allNouns) > 2:
                descriptiveNoun += "_" + child.text.lower() + "_" + relevantNouns[0].text.lower()
                nouns.remove(relevantNouns[0])
                #print(nouns)

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

    # might delete these functions
    def getModifiers(self, sentence):
        verb_modifier = [token.text for token in sentence.doc if
                         token.tag_ == 'JJR' or token.dep_ == "acomp" or token.dep_ == "attr"]
        # print(set(verb_modifier))
        return set(verb_modifier)

    def getDeterminers(self, sentence):
        determiners = []
        if isinstance(sentence, Question):
            determiners = [token.text for token in sentence.doc if token.tag_ == "DET"]
        return set(determiners)


if __name__ == '__main__':
    # process data
    # reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    trainCorpus = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task18_train")
    testCorpus = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task18_train")

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
