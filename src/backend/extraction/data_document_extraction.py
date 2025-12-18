from typing import Any

from pydantic import BaseModel
from pydantic import Field

from ..commons import LLM
from ..learning_loop import LearningLoop
from ..prompts import Prompt


class DocumentFieldExtractionOutput(BaseModel):
    """
    Represents the extracted data from a document.
    """

    name: str = Field(description="The name of the field.")
    value: str = Field(description="The value of the field.")
    confidence: float = Field(
        description="The confidence of the classifier. e.g., 0.95"
    )
    page: int = Field(
        description="The page of the document where the field is located."
    )


class DocumentListExtractionOutput(BaseModel):
    """
    Represents a list of extracted data from a document.
    """

    extracted_fields: list[DocumentFieldExtractionOutput] = Field(
        description="A list of extracted fields, each with a name, value, confidence, and page number."
    )


class DataDocumentExtraction:
    """
    Data document extraction using a given LLM.
    """

    def __init__(
        self,
        llm_client: LLM,
        prompt: Prompt,
        learning_loop: LearningLoop,
    ):
        self._llm_client = llm_client
        self._prompt = prompt
        self._learning_loop = learning_loop

    def extract_data_document(
        self, document_content_id: str, document_type: str
    ) -> tuple[DocumentListExtractionOutput, dict[str, Any]]:
        if not self._prompt:
            raise ValueError("Unknown Prompt")

        examples_text = self._learning_loop.get_learning_context(document_type)
        print(f"examples_text => {examples_text}")

        schema = self._get_schema(document_type)

        prompt = self._prompt.create()
        prompt_schema = prompt["instruction"].replace("{SPECIFIC_SCHEMA}", schema)
        prompt_schema = prompt_schema.replace("{LEARNING_NOTES}", examples_text)

        response, usage = self._llm_client.generate(
            prompt=prompt_schema,
            model=prompt["model"],
            document_cache_id=document_content_id,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": DocumentListExtractionOutput.model_json_schema(),
                "temperature": 0.1,
            },
        )

        document_extraction = DocumentListExtractionOutput.model_validate_json(response)
        return document_extraction, usage

    def _get_schema(self, document_type: str) -> str:
        match document_type:
            case "bank_statement":
                return """{
                    "account_holder_name": "Name of the person or entity owning the account.",
                    "account_number_masked": "Last 4 digits of the account number (e.g., '****1234').",
                    "statement_start_date": "Start date of the statement period (YYYY-MM-DD).",
                    "statement_end_date": "End date of the statement period (YYYY-MM-DD).",
                    "starting_balance": "Balance at the beginning of the period (number).",
                    "ending_balance": "Balance at the end of the period (number).",
                }"""
            case "government_id":
                return """{
                    "full_name": "Full legal name as displayed on the ID.",
                    "date_of_birth": "Date of birth (YYYY-MM-DD).",
                    "id_number": "The unique license or passport number.",
                    "address": "Full residential address if present.",
                    "expiration_date": "Date the ID expires (YYYY-MM-DD).",
                }"""
            case "w9_form":
                return """{
                    "legal_name": "Name as shown on your income tax return.",
                    "ein_or_ssn": "The Employer Identification Number or Social Security Number (digits only).",
                    "business_address": "Address (number, street, and apt. or suite no.).",
                    "tax_classification": "Check the appropriate box (e.g., 'Individual/proprietor', 'C Corporation', 'S Corporation', 'Partnership', 'Trust/estate', 'LLC').",
                    "signature_present": "Boolean (true if a signature is visible in Part II, else false).",
                }"""
            case "certificate_of_insurance":
                return """{
                    "insured_name": "Name of the insured entity.",
                    "policy_number": "The policy number for General Liability or primary policy.",
                    "policy_effective_date": "Policy effective start date (YYYY-MM-DD).",
                    "policy_expiration_date": "Policy expiration date (YYYY-MM-DD).",
                    "coverage_types": "List of strings. Detect active sections like 'Commercial General Liability', 'Automobile Liability', 'Umbrella Liability', 'Workers Compensation'.",
                }"""
            case _:
                return """{
                    "suggested_label": "A short classification of what this document appears to be (e.g., 'Invoice', 'Contract', 'Bank Statement', 'Receipt').",
                    "summary": "A brief 1-sentence summary of the document contents.",
                    FIELDS THAT YOU FIND IMPORTANT IN THE DOCUMENT
                }"""
