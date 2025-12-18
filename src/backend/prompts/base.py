from abc import ABC
from abc import abstractmethod


class Prompt(ABC):
    """
    Abstract base class for document prompts.
    """

    @abstractmethod
    def create(self) -> dict:
        """
        Creates the prompt string for the document.
        """
        pass
