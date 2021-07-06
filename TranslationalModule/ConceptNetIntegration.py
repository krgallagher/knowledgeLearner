import requests


class ConceptNetIntegration:
    def __init__(self):
        self.baseAddress = 'http://api.conceptnet.io/'
        self.synonymQuery = 'query?rel=/r/Synonym&start=/c/en/'
        self.synonym = 'query?rel=/r/Synonym'
        self.node = '&node=/c/en/'
        self.other = '&other=/c/en/'

    # returns a list of verbs that "cover" all of the concepts
    # if a verb is not covered then the dictionary does nothing I guess this is okay since we might want to learn that
    # concept later on
    def synonymFinder(self, concepts):
        relations = {}
        for concept in concepts:
            query = self.baseAddress + self.synonymQuery + concept
            obj = requests.get(query).json()
            for edge in obj['edges']:
                label = edge['end']['label']
                if label not in relations.keys():
                    relations[label] = edge['weight']
                else:
                    relations[label] += edge['weight']

        synonymDictionary = {}
        #the max on the relation values is somewhat arbitrary
        while synonymDictionary.keys() != set(concepts) and max(relations.values()) > 2.0:
            maximum = max(relations, key=relations.get)
            relations.pop(maximum)
            for concept in concepts:
                if concept not in synonymDictionary.keys() and self.isSynonym(concept, maximum):
                    synonymDictionary[concept] = maximum
        return synonymDictionary

    def isSynonym(self, word1, word2):
        node = self.node + word1
        other = self.other + word2
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
    concepts = ['go', 'move', 'journey', 'travel']
    synonymDictionary = semanticNetwork.synonymFinder(concepts)
    for key in synonymDictionary.keys():
        print(key, synonymDictionary[key])
    print(semanticNetwork.isSynonym("go", "go"))
