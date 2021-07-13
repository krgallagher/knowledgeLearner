import spacy
from StoryStructure.Statement import Statement


def holdsAt(fluent, time):
    return "holdsAt(" + fluent + "," + str(time) + ")"

def happensAt(fluent, time):
    return "happensAt(" + fluent + "," + str(time) + ")"

def initiatedAt(fluent, time):
    return "initiatedAt(" + fluent + "," + str(time) + ")"

def terminatedAt(fluent, time):
    return "terminatedAt(" + fluent + "," + str(time) + ")"



class EventCalculusWrapper:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def wrap(self, statement: Statement):
        fluent = statement.getFluent()
        time = statement.getLineID()
        predicate = fluent.split("(")[0]
        # this is somewhat bad since it assumes that the predicate has at least one argument,
        # although there is an easy fix for this.
        if predicate == "be":
            eventCalculus = holdsAt(fluent, time)
        else:
            eventCalculus = happensAt(fluent, time)
        statement.setEventCalculusRepresentation(eventCalculus)


if __name__ == '__main__':
    statement1 = Statement(10, "Mary moved to the hallway.")
    statement1.setFluent("go(mary,hallway)")
    statement2 = Statement(10, "Where is Mary?")
    statement2.setFluent("be(mary,V1)")
    eventCalculusWrapper = EventCalculusWrapper()
    eventCalculusWrapper.wrap(statement1)
    eventCalculusWrapper.wrap(statement2)
    print(statement1.getLineID(), statement1.getText(), statement1.getFluent(),
          statement1.getEventCalculusRepresentation())
    print(statement2.getLineID(), statement2.getText(), statement2.getFluent(),
          statement1.getEventCalculusRepresentation())
