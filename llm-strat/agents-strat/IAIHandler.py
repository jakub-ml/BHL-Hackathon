from abc import ABC, abstractmethod


class IAIHandler(ABC):
    @abstractmethod
    def userCallAI(self, msg):
        pass

    @abstractmethod
    def verifyUnderstanding(self):
        pass
    
    @abstractmethod
    def explainQuestion(self):
        pass

    @abstractmethod
    def refineFlopsFromDescription(self):
        pass