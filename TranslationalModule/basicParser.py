import spacy
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Story
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import holdsAt, happensAt, initiatedAt, terminatedAt, wrap
from Utilities.ILASPSyntax import modeHWrapping, modeBWrapping


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


# if the noun has a child that is a coordinating conjunction then we need to create multiple predicates.


class BasicParser:
    def __init__(self, corpus):
        self.nlp = spacy.load("en_core_web_lg")  # should use large for best parsing
        self.synonymDictionary = {}
        self.previousQuestionIndex = -1
        self.conceptNet = ConceptNetIntegration()
        self.conceptsToExplore = set()
        self.corpus = corpus
        # replace this with a component that checks whether certain states have changed across the entire corpus
        for story in self.corpus:
            for statement in story:
                doc = self.nlp(statement.getText())
                root = [token for token in doc if token.head == token][0]
                if root.lemma_ != "be":
                    self.corpus.isEventCalculusNeeded = True
                    return

    def parse(self, story: Story, statement: Statement):
        self.createFluentsAndModeBiasFluents(statement)
        if isinstance(statement, Question):
            self.synonymChecker(self.conceptsToExplore)
            self.updateFluents(story, statement)
            self.setEventCalculusRepresentation(story, statement)
            self.updateModeBias(story, statement)
            index = story.getIndex(statement)
            if index + 1 == story.size():
                self.previousQuestionIndex = -1
            else:
                self.previousQuestionIndex = index

    def createFluentsAndModeBiasFluents(self, statement: Statement):
        doc = self.nlp(statement.getText())
        # creating the fluent base
        fluentBase = ""
        root = [token for token in doc if token.head == token][0]
        #TODO change it so that the adposition has to be a child of the verb.
        adposition = [token for token in doc if token.pos_ == "ADP" and ((token.head == root or token.head.pos_ == "ADV") or (token.head.dep_ == "nsubj" or token.head.dep_ == 'attr'))]
        negation = [token for token in doc if token.dep_ == 'neg' and token.tag_ == 'RB']
        verb_modifier = [token for token in doc if token.dep_ == 'acomp']
        if negation:
            statement.negatedVerb = True
        fluentBase += root.lemma_
        if verb_modifier:
            fluentBase += '_' + verb_modifier[0].lemma_
        if adposition:
            nouns = [token for token in doc if
                     token.head == adposition[0] and token.tag_ == 'NN' and hasADPChild(token, doc)]
            if nouns:
                fluentBase += '_' + nouns[0].text.lower()
            else:
                fluentBase += '_' + adposition[0].text.lower()
        # the base for the fluent has been created
        # if the statement is not a question, then add concepts to explore
        if not isinstance(statement, Question):
            conceptsToExplore = set()
            if fluentBase.split('_')[0] != 'be':
                conceptsToExplore.add(fluentBase)
            self.conceptsToExplore.update(conceptsToExplore)
        # now we need to form a statement/question fluent
        nouns = [token for token in doc if "NN" in token.tag_ and token.text.lower() not in fluentBase.split('_')]
        fluent = fluentBase + "("
        modeBiasFluent = fluent
        # -----------#
        fluents = [fluent]
        modeBiasFluents = [modeBiasFluent]
        nounsCopy = nouns.copy()
        for noun in nouns:
            if noun in nounsCopy:
                nounsCopy.remove(noun)
                # see if there are any conjunctions that we want to deal with here.
                secondaryNoun = None
                children = [child for child in noun.children if 'CC' in child.tag_]
                nounChildren = [child for child in noun.children if 'NN' in child.tag_]
                if children and len(nounChildren) == 1 and nounChildren[0] in nounsCopy:
                    secondaryNoun = nounChildren[0]
                    nounsCopy.remove(secondaryNoun)

                # for all of the current fluents, add the noun
                newFluents = []
                newModeBiasFluents = []
                for i in range(0, len(fluents)):
                    fluent1, modeBiasFluent1 = self.addNounToFluent(statement, noun, fluents[i], modeBiasFluents[i])
                    newFluents.append(fluent1)
                    newModeBiasFluents.append(modeBiasFluent1)
                    if secondaryNoun:
                        fluent2, modeBiasFluent2 = self.addNounToFluent(statement, secondaryNoun, fluents[i],
                                                                        modeBiasFluents[i])
                        newFluents.append(fluent2)
                        newModeBiasFluents.append(modeBiasFluent2)
                fluents = newFluents
                modeBiasFluents = newModeBiasFluents

        if isinstance(statement, Question):
            if "where" in statement.getText().lower() or "what" in statement.getText().lower():
                for i in range(0, len(fluents)):
                    if not fluents[i][-1] == '(':
                        fluents[i] += ','
                        modeBiasFluents[i] += ','
                    fluents[i] += "V1"
                    modeBiasFluents[i] += varWrapping('nn')
        # add the rest of everything
        for i in range(0, len(fluents)):
            fluents[i] += ")"
            modeBiasFluents[i] += ")"
        statement.setFluents(set(fluents))
        statement.setModeBiasFluents(set(modeBiasFluents))
        return

    def addNounToFluent(self, statement, noun, fluent, modeBiasFluent):
        tag = noun.tag_.lower()
        # ignore plural
        if tag == 'nns':
            tag = 'nn'
        #TODO append ADP children to the noun in some way and remove a noun while doing it
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
        if fluent[-1] != '(':
            fluent += ','
            modeBiasFluent += ','
        fluent += descriptiveNoun
        modeBiasFluent += varWrapping(tag)
        # add tag predicates
        relevantPredicate = tag + '(' + descriptiveNoun + ')'
        statement.addPredicate(relevantPredicate)
        return fluent, modeBiasFluent

    def updateFluents(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            fluents, modeBiasFluents = currentStatement.getFluents(), currentStatement.getModeBiasFluents()
            currentStatement.setFluents(self.update(fluents))
            currentStatement.setModeBiasFluents(self.update(modeBiasFluents))

    def update(self, fluents):
        newFluents = set()
        for fluent in fluents:
            splitFluent = fluent.split('(')
            predicate = splitFluent[0]
            if predicate in self.synonymDictionary.keys():
                updatedFluent = self.synonymDictionary[predicate]
            else:
                updatedFluent = predicate
            for index in range(1, len(splitFluent)):
                updatedFluent += '(' + splitFluent[index]
            newFluents.add(updatedFluent)
        return newFluents

    def setEventCalculusRepresentation(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            wrap(currentStatement)

    def updateModeBias(self, story: Story, statement: Statement):
        for index in range(self.previousQuestionIndex + 1, story.getIndex(statement) + 1):
            currentStatement = story.get(index)
            # fluent = currentStatement.getFluents()
            modeBiasFluents = currentStatement.getModeBiasFluents()
            for modeBiasFluent in modeBiasFluents:
                predicate = modeBiasFluent.split('(')[0].split('_')[0]
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
            print(sentence.getText(), sentence.getLineID(), sentence.getFluents(),
                  sentence.getEventCalculusRepresentation(), sentence.getPredicates(), sentence.getModeBiasFluents())
            if isinstance(sentence, Question):
                print(sentence.getModeBiasFluents())
    print(corpus.modeBias)
    print(parser.synonymDictionary)
