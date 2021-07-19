import spacy
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Story
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import holdsAt, happensAt, initiatedAt, terminatedAt, wrap


def modeHWrapping(predicate):
    return "#modeh(" + predicate + ")."


def modeBWrapping(predicate):
    return "#modeb(" + predicate + ")."


def varWrapping(tag):
    return "var(" + tag + ")"


def hasADPChild(noun, doc):
    return [token for token in doc if token.head == noun and token.pos_ == "ADP"]


def generateNonBeBias(modeBiasFluent):
    bias = set()
    time = varWrapping("time")
    happens = happensAt(modeBiasFluent, time)
    bias.add(modeBWrapping(happens))
    return bias


def formStatementFluent(statement: Statement, fluent, modeBiasFluent, doc):
    nouns = [token for token in doc if "NN" in token.tag_ and token.text.lower() not in fluent.split('_')]
    fluent += "("
    modeBiasFluent += "("
    for noun in nouns:
        tag = noun.tag_.lower()
        # ignore plural
        if tag == 'nns':
            tag = 'nn'
        children = [child for child in noun.children]
        newNoun = ""
        for child in children:
            if child.pos_ == "ADJ":
                if newNoun:
                    newNoun += "_"
                newNoun += child.text.lower()
        if newNoun:
            newNoun += "_"
        newNoun += noun.lemma_.lower()
        if fluent[-1] != '(':
            fluent += ','
            modeBiasFluent += ','
        fluent += newNoun
        modeBiasFluent += varWrapping(tag)
        # add tag predicates
        relevantPredicate = tag + '(' + newNoun + ')'
        statement.addPredicate(relevantPredicate)
    return fluent, modeBiasFluent


def formQuestionFluent(question: Question, fluent, modeBiasFluent, doc):
    fluent, modeBiasFluent = formStatementFluent(question, fluent, modeBiasFluent, doc)
    if "where" in question.getText() or "what" in question.getText():
        if not fluent[-1] == '(':
            fluent += ','
            modeBiasFluent += ','
        fluent += "V1"
        modeBiasFluent += varWrapping('nn')
    return fluent, modeBiasFluent


class BasicParser:
    def __init__(self, corpus):
        self.nlp = spacy.load("en_core_web_lg")  # should use large for best parsing
        self.synonymDictionary = {}
        self.previousQuestionIndex = -1
        self.conceptNet = ConceptNetIntegration()
        self.conceptsToExplore = set()
        self.corpus = corpus
        for story in self.corpus:
            for statement in story:
                doc = self.nlp(statement.getText())
                root = [token for token in doc if token.head == token][0]
                if root.lemma_ != "be":
                    self.corpus.isEventCalculusNeeded = True
                    return

    def parse(self, story: Story, statement: Statement):
        if isinstance(statement, Question):
            self.parseQuestion(statement, story)
        else:
            self.parseStatement(statement)

    def parseStatement(self, statement: Statement):
        # create the base for the fluent
        doc, fluent, modeBiasFluent = self.createFluentBase(statement)
        # extract concepts to explore from this [may be able to move this into previous method eventually]
        conceptsToExplore = set()
        if fluent.split('_')[0] != 'be':
            conceptsToExplore.add(fluent)
        fluent, modeBiasFluent = formStatementFluent(statement, fluent, modeBiasFluent, doc)
        fluent += ")"
        modeBiasFluent += ")"
        statement.setFluent(fluent)
        statement.setModeBiasFluent(modeBiasFluent)
        self.conceptsToExplore.update(conceptsToExplore)

    def createFluentBase(self, statement):
        doc = self.nlp(statement.getText())
        fluent = ""
        root = [token for token in doc if token.head == token][0]
        adposition = [token for token in doc if token.pos_ == "ADP"]
        negation = [token for token in doc if token.dep_ == 'neg' and token.tag_ == 'RB']
        verb_modifier = [token for token in doc if token.dep_ == 'acomp']
        if negation:
            statement.negatedVerb = True
        fluent += root.lemma_
        # if adposition and fluent != 'be':
        if verb_modifier:
            fluent += '_' + verb_modifier[0].lemma_
        if adposition:
            nouns = [token for token in doc if
                     token.head == adposition[0] and token.tag_ == 'NN' and hasADPChild(token, doc)]
            if nouns:
                fluent += '_' + nouns[0].text.lower()
            else:
                fluent += '_' + adposition[0].text.lower()
        modeBiasFluent = fluent
        return doc, fluent, modeBiasFluent

    def parseQuestion(self, question: Question, story: Story):
        doc, fluent, modeBiasFluent = self.createFluentBase(question)
        fluent, modeBiasFluent = formQuestionFluent(question, fluent, modeBiasFluent, doc)
        fluent += ")"
        modeBiasFluent += ')'
        question.setFluent(fluent)
        question.setModeBiasFluent(modeBiasFluent)
        self.synonymChecker(self.conceptsToExplore)
        self.updateFluents(story, question)
        self.setEventCalculusRepresentation(story, question)
        self.updateModeBias(story, question)
        index = story.getIndex(question)
        if index + 1 == story.size():
            self.previousQuestionIndex = -1
        else:
            self.previousQuestionIndex = index

    def updateFluents(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            fluent, modeBiasFluent = currentStatement.getFluent(), currentStatement.getModeBiasFluent()
            currentStatement.setFluent(self.update(fluent))
            currentStatement.setModeBiasFluent(self.update(modeBiasFluent))

    def update(self, fluent):
        splitFluent = fluent.split('(')
        predicate = splitFluent[0]
        if predicate in self.synonymDictionary.keys():
            updatedFluent = self.synonymDictionary[predicate]
        else:
            return fluent
        if len(splitFluent) == 1:
            return updatedFluent
        for index in range(1, len(splitFluent)):
            updatedFluent += '(' + splitFluent[index]
        return updatedFluent

    def setEventCalculusRepresentation(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            wrap(currentStatement)

    def updateModeBias(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            fluent = currentStatement.getFluent()
            modeBiasFluent = currentStatement.getModeBiasFluent()
            predicate = fluent.split('(')[0].split('_')[0]
            if predicate == "be":
                modeBias = self.generateBeBias(modeBiasFluent, currentStatement)
            else:
                modeBias = generateNonBeBias(modeBiasFluent)
            self.corpus.updateModeBias(modeBias)

    def generateBeBias(self, modeBiasFluent, statement: Statement):
        bias = set()
        if self.corpus.isEventCalculusNeeded:
            time = varWrapping("time")
            initiated = initiatedAt(modeBiasFluent, time)
            holds = holdsAt(modeBiasFluent, time)
            terminated = terminatedAt(modeBiasFluent, time)
            if isinstance(statement, Question):
                bias.add(modeHWrapping(initiated))
                bias.add(modeHWrapping(terminated))
            else:
                bias.add(modeBWrapping(initiated))
            bias.add(modeBWrapping(holds))
        else:
            if isinstance(statement, Question):
                bias.add(modeHWrapping(modeBiasFluent))
            else:
                bias.add(modeBWrapping(modeBiasFluent))
        return bias

    def checkCurrentSynonyms(self, concept):
        for value in self.synonymDictionary.values():
            if self.conceptNet.isSynonym(concept, value):
                self.synonymDictionary[concept] = value
                return True
        for key in self.synonymDictionary.values():
            if self.conceptNet.isSynonym(concept, key):
                self.synonymDictionary[concept] = self.synonymDictionary[key]
        return False

    def synonymChecker(self, concepts):
        conceptsCopy = concepts.copy()
        for concept in conceptsCopy:
            if concept in self.synonymDictionary.keys():
                concepts.remove(concept)
            elif concept in self.synonymDictionary.values():
                self.synonymDictionary[concept] = concept
                concepts.remove(concept)
            elif self.checkCurrentSynonyms(concept):
                concepts.remove(concept)
        learnedConcepts = self.conceptNet.synonymFinder(concepts)
        self.synonymDictionary.update(learnedConcepts)


if __name__ == '__main__':
    # process data
    # reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    reader = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task15_train")

    # get corpus
    corpus = reader.corpus

    # initialise parser
    parser = BasicParser(corpus)
    print(corpus.isEventCalculusNeeded)

    for story in reader.corpus:
        for sentence in story:
            parser.parse(story, sentence)
        for sentence in story:
            print(sentence.getText(), sentence.getLineID(), sentence.getFluent(),
                  sentence.getEventCalculusRepresentation())
            if isinstance(sentence, Question):
                print(sentence.getModeBiasFluent())
    print(corpus.modeBias)
    print(parser.synonymDictionary)
