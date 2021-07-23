import requests


class ConceptNetIntegration:
    def __init__(self):
        self.baseAddress = 'http://api.conceptnet.io/'
        self.synonymQuery = 'query?rel=/r/Synonym&start=/c/en/'
        self.mannerOfQuery = 'query?rel=/r/MannerOf&start=/c/en/'
        self.synonym = 'query?rel=/r/Synonym'
        self.node = '&node=/c/en/'
        self.other = '&other=/c/en/'

    def synonymFinder(self, concepts):
        # as a first step check whether the concepts are synonyms of each other
        synonymRelations = {}
        for concept in concepts:
            synonymRelations[concept] = 0
        for concept1 in concepts:
            for concept2 in concepts:
                if self.isSynonym(concept1, concept2):
                    synonymRelations[concept1] += 1
                    synonymRelations[concept2] += 1

        currentDictionary = {}
        # while the set of keys is not empty
        size = len(synonymRelations.keys())
        for i in range(0, size):
            values = currentDictionary.values()
            keys = currentDictionary.keys()
            maximum = max(synonymRelations, key=synonymRelations.get)
            synonymRelations.pop(maximum)
            # check if it covers more than one concept
            conceptsCovered = []
            for concept in concepts:
                if concept in values:
                    currentDictionary[concept] = concept
                for key in keys:
                    if self.isSynonym(concept, key):
                        currentDictionary[concept] = currentDictionary[key]
                if concept not in currentDictionary.keys() and self.isSynonym(concept, maximum):
                    conceptsCovered.append(concept)
            if len(conceptsCovered) >= 2:
                for concept in conceptsCovered:
                    currentDictionary[concept] = maximum
        return currentDictionary

    def isSynonym(self, word1, word2):
        node = self.node + word1
        other = self.other + word2
        query = self.baseAddress + self.synonym + node + other
        obj = requests.get(query).json()
        if obj['edges']:
            return True
        if '_' in word1 and '_' in word2:  # not perfect but maybe better?
            node = self.node + word1.split('_')[0]
            other = self.other + word2.split('_')[0]
            query = self.baseAddress + self.synonym + node + other
            obj = requests.get(query).json()
            if obj['edges']:
                return True
        return False


class QueryBuilder:
    def __init__(self, start=None, end=None, rel=None, node=None, other=None, sources=None):
        self.start = start  # a URI that the start or subject position must match.
        self.end = end  # a URI that the end or object position must match
        self.rel = rel  # a relation
        self.node = node  # a URI that must match either the start or the end
        self.other = other  # a URI that must match either the start or the end, and be different from node
        self.sources = sources  # a URI that must match one of the sources of the edge
        self.baseAddress = 'http://api.conceptnet.io/'

    def withStart(self, start):
        self.start = start

    def withEnd(self, end):
        self.end = end

    def withRel(self, rel):
        self.rel = rel

    def withNode(self, node):
        self.node = node

    def withOther(self, other):
        self.other = other

    def withSources(self, sources):
        self.sources = sources

    def build(self):
        return


class Query:
    pass


if __name__ == '__main__':
    semanticNetwork = ConceptNetIntegration()
    print(semanticNetwork.isSynonym("go_to", "move_to"))
