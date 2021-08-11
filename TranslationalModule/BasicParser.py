import re
import spacy
from DatasetReader.bAbIReader import bAbIReader
from StoryStructure import Story
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from Utilities.ILASPSyntax import varWrapping, constWrapping, createConstantTerm


def createPronounRegularExpression(pronoun):
    return re.compile("(^| )" + pronoun + "( |[.!?]$)")


def createNameRegularExpression(name):
    return "\\1" + name + "\\2"


def isDisjunctive(noun, statement: Statement):
    conjunctives = [token.text.lower() for token in statement.doc if token.head == noun and token.pos_ == "CCONJ"]
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


def hasDativeParent(token):
    return token.head.dep_ == "dative"


class BasicParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")  # should use large for best parsing
        self.synonymDictionary = {}
        self.conceptNet = ConceptNetIntegration()
        self.conceptsToExplore = set()
        self.determiningConcepts = {}
        self.temporalConstants = {}

    def coreferenceFinder(self, statement: Statement, story: Story):
        index = story.getIndex(statement)
        sentenceDoc = self.nlp(statement.text)
        personalPronoun = [token for token in sentenceDoc if token.tag_ == "PRP"]
        if index == 0 or not personalPronoun:
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
        return personalPronoun[0].text, possibleReferences

    def parse(self, statement: Statement):
        usedTokens = []

        negation = [token for token in statement.doc if token.dep_ == 'neg' and token.tag_ == 'RB']
        if negation:
            statement.negatedVerb = True

        # might want to add the W pronouns into this mix and maybe also need to rename this...
        nounsAndAdjectiveComplements = [token for token in statement.doc if
                                        "NN" in token.tag_ or "JJ" in token.tag_ or "W" in token.tag_]

        fluentBase = self.createFluentBase(usedTokens, statement)

        fluent = fluentBase + "("
        statement.setFluents([[fluent]])
        statement.setModeBiasFluents([[fluent]])

        if isinstance(statement, Question):
            self.createMainPortionOfFluentForQuestion(nounsAndAdjectiveComplements, statement, usedTokens)
        else:
            if fluentBase.split('_')[0] != 'be':
                self.conceptsToExplore.add(fluentBase)
            self.createMainPortionOfFluent(nounsAndAdjectiveComplements, statement, usedTokens)

        for i in range(0, len(statement.fluents)):
            for j in range(0, len(statement.fluents[i])):
                statement.fluents[i][j] += ")"
                statement.modeBiasFluents[i][j] += ")"

    def createMainPortionOfFluentForQuestion(self, nounsAndAdjectiveComplements, question: Question, usedTokens):
        self.createMainPortionOfFluent(nounsAndAdjectiveComplements, question, usedTokens)
        if not question.isYesNoMaybeQuestion():
            self.addVariable(question)

            # TODO for afterwards: get rid of nounsCopy and condense into the used tokens section

    def createMainPortionOfFluent(self, nouns, statement, usedTokens):
        nounsCopy = nouns.copy()
        nouns = self.orderNouns(nouns, statement)
        for noun in nouns:
            self.considerNounForFluent(noun, nouns, nounsCopy, statement, usedTokens)

    def considerNounForFluent(self, noun, nouns, nounsCopy, statement, usedTokens):
        whDeterminer = [token for token in noun.children if token.tag_ == "WDT"]
        if whDeterminer:
            usedTokens.append(noun)
        if noun in nounsCopy and noun not in usedTokens:
            disjunctive = isDisjunctive(noun, statement)
            conjuncts = [noun] + list(noun.conjuncts)
            for conjunct in conjuncts:
                nounsCopy.remove(conjunct)
            newFluents = []
            newMBFluents = []
            if disjunctive:
                self.addDisjunctionToFluents(conjuncts, newFluents, newMBFluents, nouns, nounsCopy, statement)
            else:
                self.addConjunctionToFluents(conjuncts, newFluents, newMBFluents, nouns, nounsCopy, statement)
            statement.setFluents(newFluents)
            statement.setModeBiasFluents(newMBFluents)

    def addConjunctionToFluents(self, conjuncts, newFluents, newMBFluents, nouns, nounsCopy, statement):
        for i in range(0, len(statement.fluents)):
            for conjunct in conjuncts:
                fluents1 = []
                mbfluents1 = []
                for j in range(0, len(statement.fluents[i])):
                    resultingFluent, resultingMBFluent = self.addNounToFluent(statement, conjunct,
                                                                              statement.fluents[i][j],
                                                                              statement.modeBiasFluents[i][
                                                                                  j],
                                                                              nounsCopy, nouns)
                    fluents1.append(resultingFluent)
                    mbfluents1.append(resultingMBFluent)
                newFluents.append(fluents1)
                newMBFluents.append(mbfluents1)

    def addDisjunctionToFluents(self, conjuncts, newFluents, newMBFluents, nouns, nounsCopy, statement):
        for i in range(0, len(statement.fluents)):
            orFluentList = []
            orMBFluentList = []
            for conjunct in conjuncts:
                for j in range(0, len(statement.fluents[i])):
                    newFluent, newMBFluent = self.addNounToFluent(statement, conjunct,
                                                                  statement.fluents[i][j],
                                                                  statement.modeBiasFluents[i][j],
                                                                  nounsCopy, nouns)
                    orFluentList.append(newFluent)
                    orMBFluentList.append(newMBFluent)
            newFluents.append(orFluentList)
            newMBFluents.append(orMBFluentList)

    # basically need to replace, "what", "where" and "who" with V1s
    def addVariable(self, question: Question):
        for i in range(0, len(question.fluents)):
            for j in range(0, len(question.fluents[i])):
                if question.isWhoQuestion():
                    question.fluents[i][j] = question.fluents[i][j].replace("who", "V1")
                    if "V1" not in question.variableTypes.keys():
                        question.variableTypes["V1"] = 'nnp'
                    question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace("who", varWrapping(
                        question.variableTypes["V1"]))
                elif question.isWhereQuestion():
                    question.fluents[i][j] = question.fluents[i][j].replace("where", "V1")
                    if "V1" not in question.variableTypes.keys():
                        question.variableTypes["V1"] = 'nn'
                    question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace("where", varWrapping(
                        question.variableTypes["V1"]))
                elif question.isWhatQuestion():
                    question.fluents[i][j] = question.fluents[i][j].replace("what", "V1")
                    if "V1" not in question.variableTypes.keys():
                        question.variableTypes["V1"] = 'nn'
                    question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace("what", varWrapping(
                        question.variableTypes["V1"]))

    def createFluentBase(self, usedTokens, statement: Statement):
        nouns = [token for token in statement.doc if "NN" in token.tag_]
        root = [token for token in statement.doc if token.head == token][0]
        childVerb = [child for child in root.children if child.pos_ == 'VERB']

        if childVerb:
            root = childVerb[0]
        fluentBase = root.lemma_
        usedTokens.append(root)

        if isinstance(statement, Question) and not statement.isYesNoMaybeQuestion():
            typeDeterminer = [token.lemma_ for token in statement.doc if hasDetChild(token)]
            if typeDeterminer:
                fluentBase += "_" + typeDeterminer[0]
                statement.variableTypes["V1"] = typeDeterminer[0]
                # might want to add a check to see whether already in the dictionary although doesn't really matter
                self.createDeterminingConceptsEntry(typeDeterminer[0], fluentBase)
                return fluentBase
        # -------------------------------------------------

        verb_modifier = [token for token in statement.doc if token.tag_ == 'JJR' or token.dep_ == "acomp"]

        adposition = [token for token in statement.doc if
                      token.pos_ == "ADP" and (token.head == root or len(nouns) <= 2)]
        if verb_modifier and (len(nouns) >= 2 or isinstance(statement, Question)):
            fluentBase += '_' + verb_modifier[0].lemma_
            ADPModifierChildren = [token for token in statement.doc if
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
        if 'w' in tag:
            if noun.text.lower() == "who":
                tag = 'nnp'
            else:
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
        if self.isConstant(noun.text.lower()):
            wrapping = constWrapping(tag)
            statement.addConstantModeBias(createConstantTerm(tag, noun.text))
        else:
            wrapping = varWrapping(tag)

        modeBiasFluent += wrapping

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


    def isConstant(self, noun):
        if noun in self.temporalConstants.keys():
            return self.temporalConstants[noun]
        self.temporalConstants[noun] = self.conceptNet.hasTemporalAspect(noun)
        return self.temporalConstants[noun]

        #return
        #return noun.text.lower() in ["yesterday", "morning", "afternoon", "evening"]
        # if self.conceptNet.hasTemporalAspect(noun):
        #    return True

    def orderNouns(self, nouns, statement: Statement):
        sortedNouns = []
        nounSubject = [token for token in statement.doc if token.dep_ == "nsubj"]
        if nounSubject:
            sortedNouns.append(nounSubject[0])
            directObject = [token for token in statement.doc if token.dep_ == "dobj"]
            if directObject:
                sortedNouns.append(directObject[0])

            indirectObject = [token for token in statement.doc if token.dep_ == "pobj" and hasDativeParent(token)]
            if indirectObject:
                sortedNouns.append(indirectObject[0])

        constants = [noun for noun in nouns if self.isConstant(noun.text.lower()) and noun not in sortedNouns]
        # add everything else
        for noun in nouns:
            if noun not in sortedNouns and noun not in constants:
                sortedNouns.append(noun)
        for noun in constants:
            sortedNouns.append(noun)
        return sortedNouns


if __name__ == '__main__':
    # process data
    # reader = bAbIReader("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_train.txt")
    trainCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task5_train")
    testCorpus1 = bAbIReader("/Users/katiegallagher/Desktop/smallerVersionOfTask/task5_test")

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
