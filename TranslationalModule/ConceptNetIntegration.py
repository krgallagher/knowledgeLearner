import requests


class ConceptNetIntegration:
    def __init__(self):
        self.baseAddress = 'http://api.conceptnet.io/'
        self.synonymQuery = 'query?rel=/r/Synonym&start=/c/en/'
        self.synonym = 'query?rel=/r/Synonym'
        self.isArelation = 'query?rel=/r/IsA'
        self.mannerOf = 'query?rel=/r/MannerOf'
        self.relatedTo = 'query?rel=/r/RelatedTo'
        self.start = '&start=/c/en/'
        self.end = '&end=/c/en/'
        self.node = '&node=/c/en/'
        self.other = '&other=/c/en/'

    def similarPredicateFinder(self, concepts):
        conceptsCopy = concepts.copy()
        currentDictionary = {}
        for concept in concepts:
            values = currentDictionary.values()
            keys = currentDictionary.keys()
            if concept in conceptsCopy:
                for value in values:
                    if self.isSynonym(concept, value):
                        currentDictionary[concept] = value
                        conceptsCopy.discard(concept)
                        break
            if concept in conceptsCopy:
                for key in keys:
                    if self.isSynonym(concept, key):
                        currentDictionary[concept] = currentDictionary[key]
                        conceptsCopy.discard(concept)
                        break
            if concept not in keys and concept not in values and concept in conceptsCopy:
                for concept2 in conceptsCopy:
                    if concept != concept2 and self.isSynonym(concept, concept2):
                        currentDictionary[concept] = concept2
                        conceptsCopy.discard(concept)
                        break
        for concept in conceptsCopy:
            for concept2 in currentDictionary.keys():
                if self.isMannerOf(concept, concept2):
                    currentDictionary[concept] = currentDictionary[concept2]
                    break
        return currentDictionary

    def isMannerOf(self, concept1, concept2):
        node1 = self.start + concept1
        node2 = self.end + concept2
        query = self.baseAddress + self.mannerOf + node1 + node2
        obj = requests.get(query).json()
        if obj['edges']:
            return True
        return False

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

    def hasTemporalAspect(self, word):
        query = self.baseAddress + self.isArelation + self.start + word
        obj = requests.get(query).json()
        for edge in obj['edges']:
            end = edge["end"]
            if "day" in end["label"]:
                return True
        return False

    def isA(self, word, concept, moreSearches=True):
        start = self.start + word.replace(" ", "_")
        other = self.end + concept.replace(" ", "_")
        query = self.baseAddress + self.isArelation + start + other
        obj = requests.get(query).json()
        if obj['edges']:
            return True
        query = self.baseAddress + self.isArelation + start
        obj = requests.get(query).json()
        if moreSearches:
            for edge in obj['edges']:
                if self.isA(edge['end']['label'], concept, False):
                    return True
        return False
