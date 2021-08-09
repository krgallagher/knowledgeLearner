import re
import spacy
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Story
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from Utilities.ILASPSyntax import varWrapping


def createPronounRegularExpression(pronoun):
    return re.compile("(^| )" + pronoun + "( |[.!?]$)")


def createNameRegularExpression(name):
    return "\\1" + name + "\\2"


def isDisjunctive(noun, doc):
    conjunctives = [token.text.lower() for token in doc if token.head == noun and token.pos_ == "CCONJ"]
    return "or" in conjunctives


def hasDetChild(token):
    for child in token.children:
        if child.tag_ == "WDT":
            return True
    return False


def getSubstitutedText(pronoun, substitution, statement):
    pronounRegularExpression = createPronounRegularExpression(pronoun)
    nameRegularExpression = createNameRegularExpression(substitution)
    return re.sub(pronounRegularExpression, nameRegularExpression, statement.text)


class BasicParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")  # should use large for best parsing
        self.synonymDictionary = {}
        self.conceptNet = ConceptNetIntegration()
        self.conceptsToExplore = set()
        self.determiningConcepts = {}

    def coreferenceFinder(self, statement: Statement, story: Story):
        index = story.getIndex(statement)
        sentenceDoc = self.nlp(statement.text)
        pronoun = [token for token in sentenceDoc if token.tag_ == "PRP"]
        if index == 0 or not pronoun:
            return None, []
        possibleReferences = []
        for i in range(0, index):
            currentSentenceDoc = self.nlp(story.get(index - i - 1).text)
            properNoun = [token for token in currentSentenceDoc if token.pos_ == "PROPN"]
            if properNoun:
                replacementPhrase = properNoun[0].text
                if properNoun[0].conjuncts:
                    for noun in properNoun[0].conjuncts:
                        replacementPhrase += " and " + noun.text
                if replacementPhrase not in possibleReferences:
                    possibleReferences.append(replacementPhrase)
        return pronoun[0].text, possibleReferences

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
            if not statement.isYesNoMaybeQuestion():
                nounSubject = [token for token in doc if token.dep_ == "nsubj"]
                if nounSubject and nounSubject[0].tag_ == "WP":
                    self.addVariable(fluents, modeBiasFluents, statement)
                    fluents, modeBiasFluents = self.createMainPortionOfFluent(fluents, modeBiasFluents,
                                                                              nounsAndAdjectiveComplements,
                                                                              statement, usedTokens)
                else:
                    fluents, modeBiasFluents = self.createMainPortionOfFluent(fluents, modeBiasFluents,
                                                                              nounsAndAdjectiveComplements,
                                                                              statement, usedTokens)
                    self.addVariable(fluents, modeBiasFluents, statement)
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

    def addVariable(self, fluents, modeBiasFluents, statement):
        for i in range(0, len(fluents)):
            for j in range(0, len(fluents[i])):
                if not fluents[i][j][-1] == '(':
                    fluents[i][j] += ','
                    modeBiasFluents[i][j] += ','
                fluents[i][j] += "V1"
                if "V1" not in statement.variableTypes.keys():
                    statement.variableTypes["V1"] = 'nn'
                modeBiasFluents[i][j] += varWrapping(statement.variableTypes["V1"])

    def createFluentBase(self, usedTokens, nouns, sentence: Statement):
        root = [token for token in sentence.doc if token.head == token][0]
        childVerb = [child for child in root.children if child.pos_ == 'VERB']
        if childVerb:
            root = childVerb[0]
        fluentBase = root.lemma_
        usedTokens.append(root)

        if isinstance(sentence, Question) and not sentence.isYesNoMaybeQuestion():
            typeDeterminer = [token.lemma_ for token in sentence.doc if hasDetChild(token)]
            if typeDeterminer:
                fluentBase += "_" + typeDeterminer[0]
                sentence.variableTypes["V1"] = typeDeterminer[0]
                # might want to add a check to see whether already in the dictionary although doesn't really matter
                self.createDeterminingConceptsEntry(typeDeterminer[0], fluentBase)
                return fluentBase
        # -------------------------------------------------

        verb_modifier = [token for token in sentence.doc if token.tag_ == 'JJR' or token.dep_ == "acomp"]

        adposition = [token for token in sentence.doc if
                      token.pos_ == "ADP" and (token.head == root or len(nouns) <= 2)]
        if verb_modifier and (len(nouns) >= 2 or isinstance(sentence, Question)):
            fluentBase += '_' + verb_modifier[0].lemma_
            ADPModifierChildren = [token for token in sentence.doc if
                                   token.pos_ == "ADP" and token.head == verb_modifier[0]]
            if ADPModifierChildren:
                fluentBase += '_' + ADPModifierChildren[0].lemma_
                usedTokens.append(ADPModifierChildren[0])
            usedTokens.append(verb_modifier[0])

        if adposition and adposition[-1] not in usedTokens:
            fluentBase += '_' + adposition[-1].text.lower()
            usedTokens.append(adposition[-1])
        return fluentBase

    def addNounToFluent(self, statement: Statement, noun, fluent, modeBiasFluent, nouns, allNouns):
        tag = noun.tag_.lower()
        # ignore plural
        if tag == 'nns':
            tag = 'nn'

        # perhaps can store some data in a dictionary so that I don't do as many lookups
        for concept in self.determiningConcepts:
            if tag == "nnp":
                break
            elif noun.text in self.determiningConcepts[concept]["inclusions"]:
                tag = concept
                fluent, modeBiasFluent = self.replaceFluentBase(fluent, modeBiasFluent, concept)
                # need to replace the fluent base here
                break
            elif noun.text in self.determiningConcepts[concept]["exclusions"]:
                pass
            else:
                if self.conceptNet.isA(noun.text, concept):
                    tag = concept
                    fluent, modeBiasFluent = self.replaceFluentBase(fluent, modeBiasFluent, concept)
                    self.determiningConcepts[concept]["inclusions"].add(noun.text)
                    # break probably doesn't break out of this loop super effectively
                    break
                else:
                    self.determiningConcepts[concept]["exclusions"].add(noun.text)
        # print(self.determiningConcepts)

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

        if fluent[-1] != '(':
            fluent += ','
            modeBiasFluent += ','
        fluent += descriptiveNoun
        modeBiasFluent += varWrapping(tag)
        # add tag predicates
        relevantPredicate = tag + '(' + descriptiveNoun + ')'
        statement.addPredicate(relevantPredicate)
        return fluent, modeBiasFluent

    def replaceFluentBase(self, fluent, modeBiasFluent, concept):
        oldFluentBase = fluent.split('(')[0] + '('
        replacement = self.determiningConcepts[concept]["fluentBase"] + '('
        return fluent.replace(oldFluentBase, replacement), modeBiasFluent.replace(oldFluentBase, replacement)

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

    def createDeterminingConceptsEntry(self, entry, fluentBase):
        if entry in self.determiningConcepts.keys():
            return
        self.determiningConcepts[entry] = {}
        self.determiningConcepts[entry]["fluentBase"] = fluentBase
        self.determiningConcepts[entry]["inclusions"] = set()
        self.determiningConcepts[entry]["exclusions"] = set()


if __name__ == '__main__':
    # process data
    # reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    trainCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task15_train")
    testCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task15_train")

    # initialise parser
    parser = BasicParser()

    for story1 in trainCorpus1:
        for sentence1 in story1:
            print(sentence1.getText(), sentence1.getLineID(), sentence1.getFluents(),
                  sentence1.getEventCalculusRepresentation(), sentence1.getPredicates(), sentence1.getModeBiasFluents())
            if isinstance(sentence1, Question):
                print(sentence1.getModeBiasFluents())
    print(trainCorpus1.modeBias)
    print(parser.synonymDictionary)
