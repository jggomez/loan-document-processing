from .base import Prompt
from .load_prompts import load_prompt_yaml


class ExtractionPrompt(Prompt):
    """
    Prompt for the data extraction.
    """

    def create(self) -> dict:
        return load_prompt_yaml("prompt_data_extract")
