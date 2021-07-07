import spacy
from spacy.tokens import Doc

from StoryStructure.Statement import Statement


class eventCalculusWrapper:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def wrap(self, statement):
        fluent = statement.getLogicalRepresentation()
        time = statement.getLineID()
        predicate: Doc = self.nlp(fluent.split("(")[0])
        # this is somewhat bad since it assumes that the predicate has at least one argument,
        # although there is an easy fix for this.
        if predicate.text == "be":
            eventCalculus = "holdsAt(" + fluent + "," + str(time)+ ")."
        else:
            eventCalculus = "happensAt(" + fluent + "," + str(time) + ")."
        statement.setLogicalRepresentation(eventCalculus)


if __name__ == '__main__':
    statement1 = Statement(10, "Mary moved to the hallway." )
    statement1.setLogicalRepresentation("go(mary,hallway)")
    statement2 = Statement(10, "Where is Mary?")
    statement2.setLogicalRepresentation("be(mary,V1)")
    eventCalculusWrapper = eventCalculusWrapper()
    eventCalculusWrapper.wrap(statement1)
    eventCalculusWrapper.wrap(statement2)
    print(statement1.getLineID(), statement1.getText(), statement1.getLogicalRepresentation())
    print(statement2.getLineID(), statement2.getText(), statement2.getLogicalRepresentation())


