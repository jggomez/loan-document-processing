from typing import Any

from google.cloud import firestore

from ..classifier import DocumentClassificationOutput
from ..classifier import DocumentClassifier
from ..commons import get_llm_factory
from ..commons import GoogleCloudStorage
from ..commons import LLMFactory
from ..dashboard import calculate_cost
from ..dashboard import calculate_extraction_metrics
from ..dashboard import calculate_ops_metrics
from ..dashboard import calculate_tagging_metrics
from ..extraction import DataDocumentExtraction
from ..extraction import DocumentFieldExtractionOutput
from ..learning_loop import LearningLoop
from ..prompts import ClassifierPrompt
from ..prompts import ExtractionPrompt


class FacadeLoan:
    """
    Orchestrates the operations of the loan system.
    """

    facade = None

    def __init__(
        self,
        llm_factory: LLMFactory,
        storage_client: GoogleCloudStorage,
        bucket_name: str,
        api_key: str,
        db,
    ):
        self._llm_factory = llm_factory
        self._storage_client = storage_client
        self._bucket_name = bucket_name
        self._api_key = api_key
        self._db = db

    def classify_document(
        self, document_name: str
    ) -> tuple[DocumentClassificationOutput, str, dict[str, Any]]:
        print("document_name")
        print(document_name)

        document_url = self._storage_client.upload_file(
            bucket_name=self._bucket_name,
            source_file_name=f"resources/documents/{document_name}",
            destination_blob_name=f"loan_system/{document_name}",
        )

        gemini_llm = self._llm_factory.create_llm(
            "gemini",
            {
                "api_key": self._api_key,
            },
        )
        document_id = gemini_llm.load_document(document_url)

        document_classifier = DocumentClassifier(
            llm_client=gemini_llm,
            prompt=ClassifierPrompt(),
        )
        document_classification, usage = document_classifier.classify_document(
            document_content_id=document_id
        )

        print(f"Document Classification: {document_classification}")

        return document_classification, document_id, usage

    def document_extraction(
        self, document_id: str, document_type: str
    ) -> tuple[list[DocumentFieldExtractionOutput], dict[str, Any]]:
        gemini_llm = self._llm_factory.create_llm(
            "gemini",
            {
                "api_key": self._api_key,
            },
        )

        data_document_extraction = DataDocumentExtraction(
            llm_client=gemini_llm,
            prompt=ExtractionPrompt(),
            learning_loop=LearningLoop(db=self._db),
        )

        extraction, usage = data_document_extraction.extract_data_document(
            document_content_id=document_id,
            document_type=document_type,
        )

        print(f"Data Extraction: {extraction}")

        return extraction.extracted_fields, usage

    def save_learning_example(
        self, doc_type: str, field_name: str, ai_value: str, human_value: str
    ):
        print("Saving learning example...")
        LearningLoop(db=self._db).save_learning_example(
            doc_type,
            field_name,
            ai_value,
            human_value,
        )

    @staticmethod
    def calculate_metrics(
        classify_data: list, extraction_data: list, ops_metrics: list
    ) -> tuple[dict[Any, Any], list, dict[Any, Any]]:
        print("Calculating metrics...")
        print(f"Classify Data: {classify_data}")
        print(f"Extraction Data: {extraction_data}")
        print(f"Ops Metrics: {ops_metrics}")

        tagging_metrics = calculate_tagging_metrics(classify_data)
        extraction_metrics = calculate_extraction_metrics(extraction_data)
        ops_metrics_result = calculate_ops_metrics(ops_metrics)

        print(f"Tagging Metrics: {tagging_metrics}")
        print(f"Extraction Metrics: {extraction_metrics}")
        print(f"Ops Metrics: {ops_metrics_result}")
        return tagging_metrics, extraction_metrics, ops_metrics_result

    @staticmethod
    def calculate_cost(usage: dict) -> float:
        return calculate_cost(usage)

    @staticmethod
    def get_facade(project_id: str, bucket_name: str, api_key: str):
        if FacadeLoan.facade is None:
            FacadeLoan.facade = FacadeLoan(
                llm_factory=get_llm_factory(),
                storage_client=GoogleCloudStorage(project_id=project_id),
                bucket_name=bucket_name,
                api_key=api_key,
                db=firestore.Client(),
            )
        return FacadeLoan.facade
