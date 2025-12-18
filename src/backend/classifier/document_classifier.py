from typing import Any

from pydantic import BaseModel
from pydantic import Field

from ..commons import LLM
from ..prompts import Prompt


class DocumentClassificationOutput(BaseModel):
    document_type: str = Field(
        description="The type of the document. One of: [bank_statement, government_id, w9_form, certificate_of_insurance, unknown]"
    )
    confidence: float = Field(
        description="The confidence of the classifier. e.g., 0.95"
    )
    reasoning: str = Field(
        description="The reasoning behind the classification. e.g Detected 'Form W-9' header and tax classification checkboxes."
    )


class DocumentClassifier:
    """
    Classifies documents using a given LLM.
    """

    def __init__(self, llm_client: LLM, prompt: Prompt):
        self._llm_client = llm_client
        self._prompt = prompt

    def classify_document(
        self, document_content_id: str
    ) -> tuple[DocumentClassificationOutput, dict[str, Any]]:
        if not self._prompt:
            raise ValueError("Unknown Clasifier Prompt")

        prompt = self._prompt.create()

        response, usage = self._llm_client.generate(
            prompt=prompt["instruction"],
            model=prompt["model"],
            document_cache_id=document_content_id,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": DocumentClassificationOutput.model_json_schema(),
                "temperature": 0.1,
            },
        )

        document_classification = DocumentClassificationOutput.model_validate_json(
            response
        )
        return document_classification, usage
