import re
import spacy
from StoryStructure import Story
from StoryStructure.Corpus import Corpus
from StoryStructure.Question import Question
from StoryStructure.Statement import Statement
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from TranslationalModule.EventCalculus import initiatedAt, holdsAt, terminatedAt, happensAt
from Utilities.ILASPSyntax import varWrapping, constWrapping, createConstantTerm, modeHWrapping, modeBWrapping


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


def createTypingAtom(word, tag):
    return tag + '(' + word + ')'


def addConstantModeBias(self, sentence: Statement, corpus: Corpus):
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
        self.properNouns = set()

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

        # TODO RENAME THIS
        nounsAndAdjectiveComplements = [token for token in statement.doc if
                                        "NN" in token.tag_ or (
                                                "JJ" in token.tag_ and "NN" not in token.head.tag_) or "W" in token.tag_]

        nounsAndAdjectiveComplements = self.orderNouns(nounsAndAdjectiveComplements, statement)

        fluentBase = self.createFluentBase(usedTokens, statement)

        fluent = fluentBase + "("
        statement.setFluents([[fluent]])
        statement.setModeBiasFluents([[fluent]])

        if fluentBase.split('_')[0] != 'be':
            if isinstance(statement, Question):
                if len(fluentBase.split('_')) > 1:
                    self.conceptsToExplore.add(fluentBase)
            else:
                self.conceptsToExplore.add(fluentBase)

        self.createMainPortionOfFluent(nounsAndAdjectiveComplements, statement, usedTokens)

        for i in range(0, len(statement.fluents)):
            for j in range(0, len(statement.fluents[i])):
                statement.fluents[i][j] += ")"
                statement.modeBiasFluents[i][j] += ")"

    def createMainPortionOfFluent(self, nouns, statement, usedTokens):
        for noun in nouns:
            self.considerNounForFluent(noun, nouns, statement, usedTokens)
        if isinstance(statement, Question) and not statement.isYesNoMaybeQuestion():
            self.addVariable(statement)

    def considerNounForFluent(self, noun, nouns, statement, usedTokens):
        whDeterminer = [token for token in noun.children if token.tag_ == "WDT"]
        if whDeterminer:
            usedTokens.append(noun)

        if noun not in usedTokens:
            disjunctive = isDisjunctive(noun, statement)
            conjuncts = [noun] + list(noun.conjuncts)
            for conjunct in conjuncts:
                usedTokens.append(conjunct)
            newFluents = []
            newMBFluents = []
            if disjunctive:
                self.addDisjunctionToFluents(conjuncts, newFluents, newMBFluents, nouns, statement, usedTokens)
            else:
                self.addConjunctionToFluents(conjuncts, newFluents, newMBFluents, nouns, statement, usedTokens)
            statement.setFluents(newFluents)
            statement.setModeBiasFluents(newMBFluents)

    def addConjunctionToFluents(self, conjuncts, newFluents, newMBFluents, nouns, statement, usedTokens):
        for i in range(0, len(statement.fluents)):
            for conjunct in conjuncts:
                fluents1 = []
                mbfluents1 = []
                for j in range(0, len(statement.fluents[i])):
                    resultingFluent, resultingMBFluent = self.addNounToFluent(statement, conjunct,
                                                                              statement.fluents[i][j],
                                                                              statement.modeBiasFluents[i][j], nouns,
                                                                              usedTokens)
                    fluents1.append(resultingFluent)
                    mbfluents1.append(resultingMBFluent)
                newFluents.append(fluents1)
                newMBFluents.append(mbfluents1)

    def addDisjunctionToFluents(self, conjuncts, newFluents, newMBFluents, nouns, statement, usedTokens):
        for i in range(0, len(statement.fluents)):
            orFluentList = []
            orMBFluentList = []
            for conjunct in conjuncts:
                for j in range(0, len(statement.fluents[i])):
                    newFluent, newMBFluent = self.addNounToFluent(statement, conjunct, statement.fluents[i][j],
                                                                  statement.modeBiasFluents[i][j], nouns,
                                                                  usedTokens)
                    orFluentList.append(newFluent)
                    orMBFluentList.append(newMBFluent)
            newFluents.append(orFluentList)
            newMBFluents.append(orMBFluentList)

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
                        if "will" in question.text.lower():
                            question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace("where", constWrapping(
                                question.variableTypes["V1"]))
                            for answer in question.answer:
                                question.addConstantModeBias(createConstantTerm("nn", answer))
                        else:
                            question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace("where", varWrapping(
                                question.variableTypes["V1"]))

                elif question.isWhatQuestion():
                    question.fluents[i][j] = question.fluents[i][j].replace("what", "V1")
                    if "V1" not in question.variableTypes.keys():
                        question.variableTypes["V1"] = 'nn'

                    question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace("what", varWrapping(
                        question.variableTypes["V1"]))
                elif question.isHowManyQuestion():
                    substitution = re.compile("how_many_[A-Za-z]*(,|$)")
                    question.fluents[i][j] = re.sub(substitution, "V1\\1", question.fluents[i][j])
                    if "V1" not in question.variableTypes.keys():
                        question.variableTypes["V1"] = 'number'
                    question.modeBiasFluents[i][j] = re.sub(substitution, "const(number\\1)",
                                                            question.modeBiasFluents[i][j])
                    for answer in question.answer:
                        question.addConstantModeBias(createConstantTerm("number", answer))
                elif question.isWhyQuestion():
                    question.fluents[i][j] = question.fluents[i][j].replace("why", "V1")
                    if "V1" not in question.variableTypes.keys():
                        question.variableTypes["V1"] = 'jj'
                    question.modeBiasFluents[i][j] = question.modeBiasFluents[i][j].replace("why", constWrapping(
                        question.variableTypes["V1"]))
                    for answer in question.answer:
                        question.addConstantModeBias(createConstantTerm("jj", answer))

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
                self.createDeterminingConceptsEntry(typeDeterminer[0], fluentBase)
                return fluentBase

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

    def addNounToFluent(self, statement: Statement, noun, fluent, modeBiasFluent, allNouns, usedTokens):
        tag = noun.tag_.lower()
        if "nn" in tag:
            tag = "nn"
        # if tag == 'nns':
        #   tag = 'nn'
        # if tag == 'nn' and noun.text in self.properNouns:
        #    tag = 'nnp'

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

        if 'w' not in tag:
            statement.addPredicate(createTypingAtom(descriptiveNoun, tag))
        return fluent, modeBiasFluent

    def replaceFluentBase(self, fluent, modeBiasFluent, concept):
        oldFluentBase = fluent.split('(')[0] + '('
        replacement = self.determiningConcepts[concept]["fluentBase"] + '('
        return fluent.replace(oldFluentBase, replacement), modeBiasFluent.replace(oldFluentBase, replacement)

    def updateSentence(self, sentence: Statement):
        fluents, modeBiasFluents = sentence.getFluents(), sentence.getModeBiasFluents()
        sentence.setFluents(self.update(fluents))
        sentence.setModeBiasFluents(self.update(modeBiasFluents))

    # Does not work for the event calculus representation
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

    # could check if will is in the sentence and then append the direct object?
    def isConstant(self, noun):
        nounText = noun.text.lower()
        if nounText in self.temporalConstants.keys():
            return self.temporalConstants[nounText]
        elif noun.tag_.lower() == "jj":
            return True
        self.temporalConstants[nounText] = self.conceptNet.hasTemporalAspect(nounText)
        return self.temporalConstants[nounText]

    def getProperNouns(self, sentence):
        properNouns = [token.text.lower() for token in sentence.doc if token.tag_ == "NNP"]
        return set(properNouns)

    def orderNouns(self, nouns, statement: Statement):
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

    @staticmethod
    def generateBeAndQuestionBias(modeBiasFluent, statement: Statement):
        nonECBias = set()
        ECBias = set()
        time = varWrapping("time")
        if isinstance(statement, Question):
            ECBias.add(modeHWrapping(initiatedAt(modeBiasFluent, time)))
            ECBias.add(modeHWrapping(terminatedAt(modeBiasFluent, time)))
            nonECBias.add(modeHWrapping(modeBiasFluent))
        else:
            ECBias.add(modeBWrapping(initiatedAt(modeBiasFluent, time)))
            nonECBias.add(modeBWrapping(modeBiasFluent))
        ECBias.add(modeBWrapping(holdsAt(modeBiasFluent, time)))
        return nonECBias, ECBias

    @staticmethod
    def generateNonBeBias(modeBiasFluent, statement: Statement):
        nonECBias = set()
        ECBias = set()
        time = varWrapping("time")
        ECBias.add(modeBWrapping(happensAt(modeBiasFluent, time)))
        if isinstance(statement, Question):
            nonECBias.add(modeHWrapping(modeBiasFluent))
        else:
            nonECBias.add(modeBWrapping(modeBiasFluent))
        return nonECBias, ECBias

    def addStatementModeBias(self, statement):
        modeBiasFluents = statement.getModeBiasFluents()
        ECModeBias = set()
        nonECModeBias = set()
        for i in range(0, len(modeBiasFluents)):
            for j in range(0, len(modeBiasFluents[i])):
                modeBiasFluent = modeBiasFluents[i][j]
                predicate = modeBiasFluent.split('(')[0].split('_')[0]
                if predicate == "be" or isinstance(statement, Question):
                    newNonECModeBias, newECModeBias = self.generateBeAndQuestionBias(modeBiasFluent, statement)
                else:
                    newNonECModeBias, newECModeBias = self.generateNonBeBias(modeBiasFluent, statement)
                ECModeBias.update(newECModeBias)
                nonECModeBias.update(newNonECModeBias)
        return nonECModeBias, ECModeBias
