from DatasetReader.bAbIReader import bAbIReader
from StoryStructure.Question import Question
from TranslationalModule.ConceptNetIntegration import ConceptNetIntegration
from basicParser import Parser


class bAbIParser:
    def __init__(self, filename):
        self.reader = bAbIReader(filename)
        self.parser = Parser()
        self.conceptNet = ConceptNetIntegration()
        self.synonymDictionary = {}
        for story in self.reader.corpus:
            statements = story.getSentences()
            conceptsToExplore = []
            for statement in statements:
                if isinstance(statement, Question):
                    fluent, concepts = self.parser.parseQuestion(statement)
                    self.synonymChecker(conceptsToExplore)

                    # maybe we should not clear the concepts and only delete the ones we have linked up
                    # might be difficult to edit the fluent later on
                    # conceptsToExplore.clear()
                else:
                    fluent, concepts = self.parser.parseStatement(statement)
                    conceptsToExplore += concepts

            statement.setLogicalRepresentation(fluent)
        print(self.synonymDictionary)

    def checkCurrentSynonyms(self, concept):
        for value in self.synonymDictionary.values():
            if self.conceptNet.isSynonym(concept, value):
                self.synonymDictionary[concept] = value
                return True
        return False


    def synonymChecker(self, concepts):
        # conceptsToBeLearned = concepts.copy()
        for concept in concepts:
            if concept in self.synonymDictionary.keys():
            # conceptsToBeLearned.remove(concept)
                concepts.remove(concept)
            elif self.checkCurrentSynonyms(concept):
                concepts.remove(concept)
            # conceptsToBeLearned.remove(concept)
            concepts.remove(concept)

        # learnedConcepts = self.conceptNet.synonymFinder(conceptsToBeLearned)
        learnedConcepts = self.conceptNet.synonymFinder(concepts)
        self.synonymDictionary.update(learnedConcepts)

    # for each of the concepts we need to check whether or not it is already in the synonym dictionary
    # if it is then good, otherwise check the synonyms that have been learned and see if there is a relation.
    # If there is no such relation, then have a new concept learning task.





def __str__(self):
    for fluent in self.fluents:
        print(fluent)


if __name__ == '__main__':
    parser = bAbIParser("/Users/katiegallagher/Desktop/tasks_1-20_v1-2/en/qa1_single-supporting-fact_train.txt")
    for story in parser.reader.corpus:
        statements = story.getSentences()
        """
        for statement in statements:
            print(statement.getLineID(), statement.getText(), statement.getLogicalRepresentation())
    print(parser)
    """
