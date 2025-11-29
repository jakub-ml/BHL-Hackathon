from openAIHandler import OpenAIHandler


def askAgents(userProjectDescription):
    AIHandler = OpenAIHandler()
    response = AIHandler.userCallAI(userProjectDescription)
    return response[0]['compute']
