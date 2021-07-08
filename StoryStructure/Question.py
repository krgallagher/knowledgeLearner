from StoryStructure.Statement import Statement


class Question(Statement):
    def __init__(self, text, lineId, answer, hints):
        Statement.__init__(self, text, lineId)
        self.answer = answer
        self.hints = hints

# might be able to drop the hints since they aren't very helpful
