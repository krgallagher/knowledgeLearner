from StoryStructure.Question import Question
from StoryStructure.Statement import Statement

def holdsAt(fluent, time):
    return "holdsAt(" + fluent + "," + str(time) + ")"

def happensAt(fluent, time):
    return "happensAt(" + fluent + "," + str(time) + ")"

def initiatedAt(fluent, time):
    return "initiatedAt(" + fluent + "," + str(time) + ")"

def terminatedAt(fluent, time):
    return "terminatedAt(" + fluent + "," + str(time) + ")"

#TODO fix so that it doesn't rely on there being one argument for the predicate.
def wrap(statement: Statement):
    fluents = statement.getFluents()
    eventCalculusPredicates = []
    time = statement.getLineID()
    for i in range(0, len(fluents)):
        currentECPredicates = []
        for j in range(0, len(fluents[i])):
            fluent = fluents[i][j]
            predicate = fluent.split("(")[0].split('_')[0]
            if predicate == "be":
                if statement.negatedVerb:
                    eventCalculus = terminatedAt(fluent, time)
                elif isinstance(statement, Question):
                    eventCalculus = holdsAt(fluent, time)
                else:
                    eventCalculus = initiatedAt(fluent, time)
            else:
                eventCalculus = happensAt(fluent, time)
            currentECPredicates.append(eventCalculus)
        eventCalculusPredicates.append(currentECPredicates)
    statement.setEventCalculusRepresentation(eventCalculusPredicates)
