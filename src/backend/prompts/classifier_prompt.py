from .base import Prompt
from .load_prompts import load_prompt_yaml


class ClassifierPrompt(Prompt):
    """
    Prompt for the Classifier.
    """

    def create(self) -> dict:
        return load_prompt_yaml("prompt_classifier")
