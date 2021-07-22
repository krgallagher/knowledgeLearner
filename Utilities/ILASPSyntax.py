from StoryStructure.Question import Question


def createTimeRange(time: int):
    return 'time(1..' + str(time) + ')'


def modeHWrapping(predicate):
    return "#modeh(" + predicate + ")."


def modeBWrapping(predicate):
    return "#modeb(" + predicate + ")."
