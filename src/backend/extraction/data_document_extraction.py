from typing import Any

import fitz
from google.genai import types
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
    coordinates: list[int] = Field(
        description="The coordinates of the field in the document."
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
                "thinking_config": types.ThinkingConfig(thinking_level="minimal"),
                "media_resolution": types.MediaResolution.MEDIA_RESOLUTION_HIGH,
            },
        )

        document_extraction = DocumentListExtractionOutput.model_validate_json(response)
        return document_extraction, usage

    def draw_from_model_coords(
        self,
        pdf_path: str,
        extracted_fields: list[DocumentFieldExtractionOutput],
    ) -> str:
        doc = fitz.open(pdf_path)

        for field in extracted_fields:
            if field.page > len(doc) or not field.coordinates:
                continue

            page = doc[field.page - 1]
            w, h = page.rect.width, page.rect.height

            if field.coordinates:
                ymin, xmin, ymax, xmax = field.coordinates

                rect = fitz.Rect(
                    (xmin / 1000) * w,
                    (ymin / 1000) * h,
                    (xmax / 1000) * w,
                    (ymax / 1000) * h,
                )

                if page.rotation != 0:
                    matrix = ~page.rotation_matrix
                    rect_final = rect * matrix
                else:
                    rect_final = rect

                rect_final.normalize()

                if rect_final.width == 0:
                    rect_final.x1 += 1
                if rect_final.height == 0:
                    rect_final.y1 += 1

                if rect_final.is_empty or rect_final.is_infinite:
                    continue

                try:
                    annot = page.add_rect_annot(rect_final)
                    annot.set_colors(stroke=(1, 0, 0))
                    annot.set_border(width=2)
                    annot.update()
                except ValueError as e:
                    print(f"Error adding annotation for {field}: {e}")
                    continue

        output_path = pdf_path.replace(".pdf", "_annotated.pdf")

        doc.save(output_path, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()
        return output_path

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
