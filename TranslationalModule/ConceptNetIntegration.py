import requests


class ConceptNetIntegration:
    def __init__(self):
        self.baseAddress = 'http://api.conceptnet.io/'
        self.synonymQuery = 'query?rel=/r/Synonym&start=/c/en/'
        self.mannerOfQuery = 'query?rel=/r/MannerOf&start=/c/en/'
        self.synonym = 'query?rel=/r/Synonym'
        self.relatedTo = 'query?rel=/r/RelatedTo'
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

    # NOTE: this may not be the best, route, but let's just do this for now
    def isSynonym(self, word1, word2):
        root1 = word1.split('_')[0]
        root2 = word2.split('_')[0]
        if root1 == root2:
            return True
        node = self.node + word1
        other = self.other + word2
        query = self.baseAddress + self.synonym + node + other
        obj = requests.get(query).json()
        if obj['edges']:
            return True
        if '_' in word1 and '_' in word2:
            node = self.node + root1
            other = self.other + root2
            if node == other:
                return True
            query = self.baseAddress + self.synonym + node + other
            obj = requests.get(query).json()
            if obj['edges']:
                return True
        return False

    def isRelated(self, word1, word2):
        node = self.node + word1
        other = self.other + word2
        query = self.baseAddress + self.relatedTo + node + other
        obj = requests.get(query).json()
        if obj['edges']:
            return True


if __name__ == '__main__':
    semanticNetwork = ConceptNetIntegration()
    print(semanticNetwork.isSynonym("take", "carry"))
