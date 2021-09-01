import re
import spacy
from StoryStructure import Story
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from StoryStructure.Sentence import Sentence
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from Utilities.ILASPSyntax import varWrapping, constWrapping, createConstantTerm


def createPronounRegularExpression(pronoun):
    return re.compile("(^| )" + pronoun + "( |[.!?]$)")


def createNameRegularExpression(name):
    return "\\1" + name + "\\2"


def isDisjunctive(noun, statement: Sentence):
    conjunctives = [token.text.lower() for token in statement.doc if token.head == noun and token.pos_ == "CCONJ"]
    return "or" in conjunctives


def hasWHDeterminerChild(token):
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


def createTypingAtom(word, tag):
    return tag + '(' + word + ')'


def addConstantModeBias(self, sentence: Sentence, corpus: Corpus):
    for constantBias in sentence.constantModeBias:
        corpus.addConstantModeBias(constantBias)


class BasicParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        self.synonymDictionary = {}
        self.conceptNet = ConceptNetIntegration()
        self.conceptsToExplore = set()
        self.determiningConcepts = {}
        self.temporalConstants = {}

    def coreferenceFinder(self, statement: Sentence, story: Story):
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

    def parse(self, statement: Sentence):
        usedTokens = []

        negation = [token for token in statement.doc if token.dep_ == 'neg' and token.tag_ == 'RB']
        if negation:
            statement.negatedVerb = True

        predicate = self.createPredicate(usedTokens, statement)

        fluent = predicate + "("
        statement.setFluents([[fluent]])
        statement.setModeBiasFluents([[fluent]])

        if predicate.split('_')[0] != 'be':
            if isinstance(statement, Question):
                if len(predicate.split('_')) > 1:
                    self.conceptsToExplore.add(predicate)
            else:
                self.conceptsToExplore.add(predicate)

        possibleArguments = [token for token in statement.doc if "NN" in token.tag_ or (
                "JJ" in token.tag_ and "NN" not in token.head.tag_) or "W" in token.tag_]

        possibleArguments = self.orderNouns(possibleArguments, statement)

        self.createMainPortionOfFluent(possibleArguments, statement, usedTokens)

        for i in range(0, len(statement.fluents)):
            for j in range(0, len(statement.fluents[i])):
                statement.fluents[i][j] += ")"
                statement.modeBiasFluents[i][j] += ")"

    def createMainPortionOfFluent(self, possibleArgs, statement, usedTokens):
        for possArg in possibleArgs:
            self.considerNounForFluent(possArg, possibleArgs, statement, usedTokens)
        if isinstance(statement, Question) and not statement.isYesNoMaybeQuestion():
            self.addVariable(statement)

    def considerNounForFluent(self, possArg, possibleArgs, statement, usedTokens):
        whDeterminer = [token for token in possArg.children if token.tag_ == "WDT"]
        if whDeterminer:
            usedTokens.append(possArg)

        if possArg not in usedTokens:
            disjunctive = isDisjunctive(possArg, statement)
            conjuncts = [possArg] + list(possArg.conjuncts)
            for conjunct in conjuncts:
                usedTokens.append(conjunct)
            newFluents = []
            newMBFluents = []
            if disjunctive:
                self.addDisjunctionToFluents(conjuncts, newFluents, newMBFluents, possibleArgs, statement, usedTokens)
            else:
                self.addConjunctionToFluents(conjuncts, newFluents, newMBFluents, possibleArgs, statement, usedTokens)
            statement.setFluents(newFluents)
            statement.setModeBiasFluents(newMBFluents)

    def addConjunctionToFluents(self, conjuncts, newFluents, newMBFluents, possArgs, statement, usedTokens):
        for i in range(0, len(statement.fluents)):
            for conjunct in conjuncts:
                fluents1 = []
                mbFluents1 = []
                for j in range(0, len(statement.fluents[i])):
                    resultingFluent, resultingMBFluent = self.addNounToFluent(statement, conjunct,
                                                                              statement.fluents[i][j],
                                                                              statement.modeBiasFluents[i][j], possArgs,
                                                                              usedTokens)
                    fluents1.append(resultingFluent)
                    mbFluents1.append(resultingMBFluent)
                newFluents.append(fluents1)
                newMBFluents.append(mbFluents1)

    def addDisjunctionToFluents(self, conjuncts, newFluents, newMBFluents, possArgs, statement, usedTokens):
        for i in range(0, len(statement.fluents)):
            orFluentList = []
            orMBFluentList = []
            for conjunct in conjuncts:
                for j in range(0, len(statement.fluents[i])):
                    newFluent, newMBFluent = self.addNounToFluent(statement, conjunct, statement.fluents[i][j],
                                                                  statement.modeBiasFluents[i][j], possArgs,
                                                                  usedTokens)
                    orFluentList.append(newFluent)
                    orMBFluentList.append(newMBFluent)
            newFluents.append(orFluentList)
            newMBFluents.append(orMBFluentList)

    def whoWhereWhatAddArgument(self, question: Question, qName, varType, i, j):
        question.fluents[i][j] = question.fluents[i][j].replace(qName, "V1")
        if "V1" not in question.variableTypes.keys():
            question.variableTypes["V1"] = varType
        if "will" in question.text.lower():
            question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace(qName, constWrapping(
                question.variableTypes["V1"]))
            for answer in question.answer:
                question.addConstantModeBias(createConstantTerm(varType, answer))
        else:
            question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace(qName, varWrapping(
                question.variableTypes["V1"]))

    def addVariable(self, question: Question):
        for i in range(0, len(question.fluents)):
            for j in range(0, len(question.fluents[i])):
                if question.isWhoQuestion():
                    self.whoWhereWhatAddArgument(question, "who", "nnp", i, j)
                elif question.isWhereQuestion():
                    self.whoWhereWhatAddArgument(question, "where", "nn", i, j)
                elif question.isWhatQuestion():
                    self.whoWhereWhatAddArgument(question, "what", "nn", i, j)
                elif question.isWhyQuestion():
                    question.fluents[i][j] = question.fluents[i][j].replace("why", "V1")
                    if "V1" not in question.variableTypes.keys():
                        question.variableTypes["V1"] = 'jj'
                    question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace("why", constWrapping(
                        question.variableTypes["V1"]))
                    for answer in question.answer:
                        question.addConstantModeBias(createConstantTerm("jj", answer))
                elif question.isHowManyQuestion():
                    substitution = re.compile("how_many_[A-Za-z]*(,|$)")
                    question.fluents[i][j] = re.sub(substitution, "V1\\1", question.fluents[i][j])
                    if "V1" not in question.variableTypes.keys():
                        question.variableTypes["V1"] = 'number'
                    question.modeBiasFluents[i][j] = re.sub(substitution, "const(number\\1)",
                                                            question.modeBiasFluents[i][j])
                    for answer in question.answer:
                        question.addConstantModeBias(createConstantTerm("number", answer))

    def createPredicate(self, usedTokens, statement: Sentence):
        root = [token for token in statement.doc if token.head == token][0]
        childVerb = [child for child in root.children if child.pos_ == 'VERB']

        if childVerb:
            root = childVerb[0]
        fluentBase = root.lemma_
        usedTokens.append(root)

        if isinstance(statement, Question) and not statement.isYesNoMaybeQuestion():
            typeDeterminer = [token.lemma_ for token in statement.doc if hasWHDeterminerChild(token)]
            if typeDeterminer:
                fluentBase += "_" + typeDeterminer[0]
                statement.variableTypes["V1"] = typeDeterminer[0]
                self.createDeterminingConceptsEntry(typeDeterminer[0], fluentBase)
                return fluentBase

        verb_modifier = [token for token in statement.doc if token.tag_ == 'JJR' or token.dep_ == "acomp"]

        nouns = [token for token in statement.doc if "NN" in token.tag_]

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

    def addNounToFluent(self, statement: Sentence, noun, fluent, modeBiasFluent, allNouns, usedTokens):
        tag = noun.tag_.lower()
        if tag == 'nns':
            tag = 'nn'

        for concept in self.determiningConcepts:
            if tag == "nnp":
                break
            elif noun.text in self.determiningConcepts[concept]["inclusions"]:
                tag = concept
                fluent, modeBiasFluent = self.replaceFluentBase(fluent, modeBiasFluent, concept)
                break
            elif noun.text in self.determiningConcepts[concept]["exclusions"]:
                pass
            else:
                if self.conceptNet.isA(noun.text, concept):
                    tag = concept
                    fluent, modeBiasFluent = self.replaceFluentBase(fluent, modeBiasFluent, concept)
                    self.determiningConcepts[concept]["inclusions"].add(noun.text)
                    break
                else:
                    self.determiningConcepts[concept]["exclusions"].add(noun.text)

        descriptiveNoun, tag = self.addAdjectiveChildren(noun, usedTokens, tag)

        if descriptiveNoun:
            descriptiveNoun += "_"
        descriptiveNoun += noun.lemma_.lower()
        children = [child for child in noun.children]
        for child in children:
            if child.pos_ == "ADP" and len(allNouns) > 2 and child not in usedTokens:
                relevantNouns = [aChild for aChild in child.children if "NN" in aChild.tag_]
                descriptiveNoun += "_" + child.text.lower() + "_" + relevantNouns[0].text.lower()
                usedTokens.append(relevantNouns[0])

        if fluent[-1] != '(':
            fluent += ','
            modeBiasFluent += ','
        fluent += descriptiveNoun
        if self.isConstant(noun):
            wrapping = constWrapping(tag)
            statement.addConstantModeBias(createConstantTerm(tag, noun.text))
        elif 'w' in tag:
            wrapping = descriptiveNoun
        else:
            wrapping = varWrapping(tag)
        modeBiasFluent += wrapping

        return fluent, modeBiasFluent

    def replaceFluentBase(self, fluent, modeBiasFluent, concept):
        oldFluentBase = fluent.split('(')[0] + '('
        replacement = self.determiningConcepts[concept]["fluentBase"] + '('
        return fluent.replace(oldFluentBase, replacement), modeBiasFluent.replace(oldFluentBase, replacement)

    def updateSentence(self, sentence: Sentence):
        fluents, modeBiasFluents = sentence.getFluents(), sentence.getModeBiasFluents()
        sentence.setFluents(self.updateFluentAndMBFluent(fluents))
        sentence.setModeBiasFluents(self.updateFluentAndMBFluent(modeBiasFluents))

    def updateFluentAndMBFluent(self, fluents):
        newFluents = []
        for i in range(0, len(fluents)):
            currentFluents = []
            for j in range(0, len(fluents[i])):
                predicate = fluents[i][j].split('(')[0]
                if predicate in self.synonymDictionary.keys():
                    updatedFluent = self.synonymDictionary[predicate]
                else:
                    updatedFluent = predicate
                updatedFluent = fluents[i][j].replace(predicate + '(', updatedFluent + '(')
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
        nounText = noun.text.lower()
        if nounText in self.temporalConstants.keys():
            return self.temporalConstants[nounText]
        for concept in self.determiningConcepts:
            if noun.text in self.determiningConcepts[concept]["inclusions"]:
                return False
        if noun.tag_.lower() == "jj":
            return True
        self.temporalConstants[nounText] = self.conceptNet.hasTemporalAspect(nounText)
        return self.temporalConstants[nounText]

    def getProperNouns(self, sentence):
        properNouns = [token.text.lower() for token in sentence.doc if token.tag_ == "NNP"]
        return set(properNouns)

    def orderNouns(self, nouns, statement: Sentence):
        sortedNouns = []
        nounSubject = [token for token in statement.doc if token.dep_ == "nsubj"]
        if nounSubject:
            sortedNouns.append(nounSubject[-1])
            directObject = [token for token in statement.doc if token.dep_ == "dobj"]
            if directObject:
                sortedNouns.append(directObject[0])

            indirectObject = [token for token in statement.doc if token.dep_ == "pobj" and hasDativeParent(token)]
            if indirectObject:
                sortedNouns.append(indirectObject[0])

        constants = [noun for noun in nouns if self.isConstant(noun) and noun not in sortedNouns]

        questionWords = [noun for noun in nouns if "W" in noun.tag_ and noun not in sortedNouns]

        for noun in nouns:
            if noun not in sortedNouns and noun not in constants and noun not in questionWords:
                sortedNouns.append(noun)
        for noun in constants:
            sortedNouns.append(noun)
        for noun in questionWords:
            sortedNouns.append(noun)
        return sortedNouns

    def addAdjectiveChildren(self, noun, usedTokens, tag, base=""):
        children = [child for child in noun.children]
        for child in children:
            if (child.tag_ == "JJ" or child.tag_ == "WRB") and child not in usedTokens:
                base, tag = self.addAdjectiveChildren(child, usedTokens, tag, base)
                if base:
                    base += "_"
                base += child.text.lower()
                usedTokens.append(child)
                if child.tag_ == "WRB":
                    tag = 'wrb'
        return base, tag
