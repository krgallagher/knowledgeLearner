import requests


class ConceptNetIntegration:
    def __init__(self):
        self.baseAddress = 'http://api.conceptnet.io/'
        self.synonymQuery = 'query?rel=/r/Synonym&start=/c/en/'
        self.mannerOfQuery = 'query?rel=/r/MannerOf&start=/c/en/'
        self.synonym = 'query?rel=/r/Synonym'
        self.mannerOf = 'query?rel=/r/MannerOf'
        self.relatedTo = 'query?rel=/r/RelatedTo'
        self.start = '&start=/c/en/'
        self.node = '&node=/c/en/'
        self.other = '&other=/c/en/'

    def synonymFinder(self, concepts):
        conceptsCopy = concepts.copy()
        currentDictionary = {}
        for concept in concepts:
            values = currentDictionary.values()
            keys = currentDictionary.keys()
            if concept in values:
                currentDictionary[concept] = concept
                conceptsCopy.discard(concept)
            for key in keys:
                if self.isSynonym(concept, key):
                    currentDictionary[concept] = currentDictionary[key]
                    conceptsCopy.discard(concept)
                    break
            if concept not in keys and concept not in values:
                for concept2 in conceptsCopy:
                    if concept != concept2 and self.isSynonym(concept, concept2):
                        currentDictionary[concept] = concept2
                        conceptsCopy.discard(concept)
                        break
        # if the concepts dictionary is not empty then try and relate these words in another way...
        for concept in conceptsCopy:
            self.isMannerOf(concept, currentDictionary)
        print(conceptsCopy)
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

    def isMannerOf(self, word, currentDictionary):
        # create the query
        node = self.node + word
        query = self.baseAddress + self.mannerOf + node
        obj = requests.get(query).json()
        # might need to make a list of the possible relations here and then pick one with the highest waiting, somehow
        # relations = set()
        for edge in obj['edges']:
            start = edge["start"]
            end = edge["end"]
            if start["label"].replace(" ", "_") != word and start["language"] == "en":
                for concept in currentDictionary.keys():
                    if self.isSynonym(start["label"].replace(" ", "_"), concept):
                        # relations.add(concept)
                        currentDictionary[word] = currentDictionary[concept]
                        print("Success!", start["label"], concept, word)
                        return
            elif end["label"].replace(" ", "_") != word and start["language"] == "en":
                for concept in currentDictionary.keys():
                    if self.isSynonym(end["label"].replace(" ", "_"), concept):
                        currentDictionary[word] = currentDictionary[concept]
                        # relations.add(concept)
                        print("Success!", start["label"], concept, word)
                        return
        # print(relations)

    def test(self, word):
        node = self.node + word
        query = self.baseAddress + self.mannerOf + node
        print(query)
        obj = requests.get(query).json()
        print(obj['edges'])


if __name__ == '__main__':
    semanticNetwork = ConceptNetIntegration()
    print(semanticNetwork.isRelated("put", "leave"))
