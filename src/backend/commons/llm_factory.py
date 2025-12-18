import io
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Type

import httpx
from google import genai


class LLM(ABC):
    """
    Abstract base class for Large Language Models.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str,
        document_cache_id: str,
        config: Dict[str, Any] = {},
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generates content based on a prompt.

        Args:
            prompt: The input prompt for the LLM.

        Returns:
            The generated content as a string.
        """
        pass

    @abstractmethod
    def load_document(self, document_path: str):
        """
        Loads a document into the LLM's cache or context.

        Args:
            document_path: The path to the document to load.
        """
        pass


class GeminiLLM(LLM):
    """
    LLM client for Google's Gemini models.
    """

    def __init__(self, api_key: str):
        """
        Initializes the Gemini LLM client.

        Args:
            api_key: The API key for the Gemini API.
        """
        self.client = genai.Client(api_key=api_key.strip())

    def generate(
        self,
        prompt: str,
        model: str,
        document_cache_id: str,
        config: Dict[str, Any] = {},
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generates content using the Gemini model.
        """
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[document_cache_id, prompt],
                config=config,
            )
            return response.text, response.usage_metadata
        except Exception as e:
            print(f"An error occurred while generating content with Gemini: {e}")
            raise

    def load_document(self, document_path: str):
        """
        Loads a document into the LLM's cache or context.

        Args:
            document_path: The path to the document to load.
        """
        try:
            doc_io = io.BytesIO(httpx.get(document_path).content)

            doc_id = self.client.files.upload(
                file=doc_io, config=dict(mime_type="application/pdf")
            )
            return doc_id
        except Exception as e:
            print(f"An error occurred while loading document with Gemini: {e}")
            raise


class LLMFactory:
    """
    Factory for creating LLM clients.
    """

    def __init__(self):
        self._llm_map: Dict[str, Type[LLM]] = {}

    def register_llm(self, llm_type: str, llm_class: Type[LLM]):
        """
        Registers a new LLM type.
        """
        if not issubclass(llm_class, LLM):
            raise TypeError("llm_class must be a subclass of LLM")
        self._llm_map[llm_type] = llm_class

    def create_llm(self, llm_type: str, config: Dict[str, Any]) -> LLM:
        """
        Creates an LLM client of the specified type.

        Args:
            llm_type: The type of LLM to create (e.g., "gemini").
            config: A dictionary of configuration parameters for the LLM.

        Returns:
            An instance of the specified LLM client.
        """
        llm_class = self._llm_map.get(llm_type)
        if not llm_class:
            raise ValueError(f"Unknown LLM type: {llm_type}")

        return llm_class(**config)


def get_llm_factory() -> LLMFactory:
    """
    Returns an instance of the LLMFactory with Gemini pre-registered.
    """
    factory = LLMFactory()
    factory.register_llm("gemini", GeminiLLM)
    return factory
