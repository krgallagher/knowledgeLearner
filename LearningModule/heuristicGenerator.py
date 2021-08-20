class HeuristicGenerator:
    def __init__(self, corpus):
        self.corpus = corpus

    def maximumNumberOfVariables(self):
        if self.corpus.isEventCalculusNeeded:
            numNeeded = 4
        else:
            numNeeded = 3
        if self.hasMBFluentWithMoreThan2NonConstArguments():
            numNeeded += 1
        return numNeeded

    def hasMBFluentWithMoreThan2NonConstArguments(self):
        for rule in self.corpus.nonECModeBias:
            if "modeb" in rule and rule.count('var') > 2:
                return True
        return False

    def maxNumberOfLiterals(self):
        maxNum = 2
        for rule in self.corpus.nonECModeBias:
            if "modeb" in rule and rule.count('var') >= 2 and rule.count('const') > 0:
                maxNum += 1
                break
        return maxNum
