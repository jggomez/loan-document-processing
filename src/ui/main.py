import os
import sys
import time
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from backend import FacadeLoan
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")


@st.cache_resource
def init_facade():
    return FacadeLoan.get_facade(
        api_key=API_KEY,
        project_id=PROJECT_ID,
        bucket_name=BUCKET_NAME,
    )


facade_loan_system = init_facade()

st.set_page_config(
    page_title="Loan Document Processing",
    page_icon="🏦",
    layout="wide",
)


def initialize_session_state():
    if "documents" not in st.session_state:
        st.session_state.documents = {}
    if "document_types" not in st.session_state:
        st.session_state.document_types = {
            "document_types": [
                "bank_statement",
                "government_id",
                "w9_form",
                "certificate_of_insurance",
                "unknown",
            ]
        }
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "confidence_thresholds": {
                "Bank Statement": 0.80,
                "Government ID": 0.90,
                "W-9": 0.85,
                "Certificate of Insurance (COI)": 0.80,
                "Unknown": 1.0,
            }
        }
    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None
    if "document_classify_review" not in st.session_state:
        st.session_state.document_classify_review = {"classify_reviews": []}
    if "document_extraction_review" not in st.session_state:
        st.session_state.document_extraction_review = {"extraction_reviews": []}


def call_document_classifier(doc_name):
    print(f"Processing document: {doc_name}")
    document_classification, document_id, classification_usage = (
        facade_loan_system.classify_document(document_name=doc_name)
    )

    predicted_type = document_classification.document_type
    confidence = document_classification.confidence

    data_extraction, extraction_usage, annoted_file = (
        facade_loan_system.document_extraction(
            document_name=doc_name,
            document_id=document_id,
            document_type=predicted_type,
        )
    )

    cost_usage = FacadeLoan.calculate_cost(
        classification_usage
    ) + FacadeLoan.calculate_cost(extraction_usage)

    document_fields = []

    for field in data_extraction:
        document_fields.append(
            {
                "name": field.name,
                "value": field.value,
                "confidence": field.confidence,
                "page": field.page,
            }
        )

    st.session_state.documents[doc_name].update(
        {
            "status": "Processed",
            "predicted_type": predicted_type,
            "type_confidence": confidence,
            "type_confidence_original": confidence,
            "fields": document_fields,
            "file": annoted_file,
        }
    )

    st.session_state.document_classify_review["classify_reviews"].append(
        {"predicted_type": predicted_type, "actual_type": predicted_type}
    )

    return cost_usage


def save_file_locally(uploaded_file):
    save_folder = "resources/documents"
    os.makedirs(save_folder, exist_ok=True)
    save_path = os.path.join(save_folder, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    initialize_session_state()
    local_css("src/ui/styles.css")

    st.markdown("# Loan Document Processing")
    st.markdown("Upload, classify, and review loan application documents.")

    st.sidebar.page_link(
        "https://storage.googleapis.com/questionsanswersproject/loan_system/examples/bank_statement_dec_2020.pdf",
        label="Example Document 1",
        icon="📄",
    )
    st.sidebar.page_link(
        "https://storage.googleapis.com/questionsanswersproject/loan_system/examples/insurance_card_2.pdf",
        label="Example Document 2",
        icon="📄",
    )
    st.sidebar.page_link(
        "https://storage.googleapis.com/questionsanswersproject/loan_system/examples/state_id.pdf",
        label="Example Document 3",
        icon="📄",
    )

    with st.sidebar:
        with st.container(border=True):
            st.header("Upload Documents")
            uploaded_files = st.file_uploader(
                "Choose PDF files to upload",
                accept_multiple_files=True,
                type=["pdf"],
                label_visibility="collapsed",
            )

            if st.button(
                "Start Processing",
                use_container_width=True,
                type="primary",
                disabled=not uploaded_files,
            ):
                for uploaded_file in uploaded_files:
                    if uploaded_file.name not in st.session_state.documents:
                        file_path = save_file_locally(uploaded_file)
                        st.session_state.documents[uploaded_file.name] = {
                            # "file": uploaded_file.getvalue(),
                            "status": "Processing",
                            "predicted_type": "Unknown",
                            "type_confidence": 0.0,
                            "fields": [],
                            "corrected_type": None,
                            "path": file_path,
                        }
                st.rerun()

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if (
                uploaded_file.name in st.session_state.documents
                and st.session_state.documents[uploaded_file.name]["status"]
                == "Processing"
            ):
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    start_time = time.time()
                    cost_usage = call_document_classifier(uploaded_file.name)
                    end_time = time.time()
                    latency_sec = end_time - start_time

                    st.session_state.documents[uploaded_file.name].update(
                        {
                            "latency_seconds": latency_sec,
                            "cost_usd": cost_usage,
                            "status": "Processed",
                        }
                    )
                st.session_state.selected_document = uploaded_file.name
                st.switch_page("pages/1_Document_View.py")
                st.rerun()

    st.header("Uploaded Documents")
    if not st.session_state.documents:
        st.info(
            "No documents uploaded yet. Use the sidebar to upload and process your first document."
        )
    else:
        doc_keys = list(st.session_state.documents.keys())

        for doc_name in doc_keys:
            doc_info = st.session_state.documents[doc_name]
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                with col1:
                    st.markdown(f"**📄 {doc_name}**")
                with col2:
                    status = doc_info.get("status", "Unknown")
                    if status == "Processed":
                        st.success(f"**Status:** {status}")
                    elif status == "Processing":
                        st.warning(f"**Status:** {status}")
                    else:
                        st.info(f"**Status:** {status}")
                with col3:
                    predicted_type = doc_info.get("predicted_type", "N/A")
                    confidence = doc_info.get("type_confidence", 0)
                    st.markdown(f"**Type:** {predicted_type} (`{confidence:.2f}`)")
                with col4:
                    if st.button(
                        "View/Edit", key=f"view_{doc_name}", use_container_width=True
                    ):
                        st.session_state.selected_document = doc_name
                        st.switch_page("pages/1_Document_View.py")


if __name__ == "__main__":
    main()
