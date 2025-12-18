import os

import pandas as pd
import streamlit as st
from backend import FacadeLoan
from dotenv import load_dotenv
from streamlit_pdf_viewer import pdf_viewer

load_dotenv()

API_KEY = os.getenv("API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")


def init_facade():
    return FacadeLoan.get_facade(
        api_key=API_KEY,
        project_id=PROJECT_ID,
        bucket_name=BUCKET_NAME,
    )


facade_loan_system = init_facade()

st.set_page_config(layout="wide")


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def document_view_page():
    local_css("src/ui/styles.css")
    st.markdown("# Document Viewer")

    if (
        "selected_document" not in st.session_state
        or not st.session_state.selected_document
    ):
        st.warning(
            "No document selected. Please go back to the main page and select a document to view."
        )
        if st.button("Back to Main Page"):
            st.switch_page("main.py")
        return

    doc_name = st.session_state.selected_document
    doc_info = st.session_state.documents[doc_name]

    if st.button("Back to Document List"):
        st.switch_page("main.py")

    left_pane, right_pane = st.columns(2)

    with left_pane:
        with st.container(border=True):
            st.header("Document Preview")
            pdf_viewer(input=doc_info["file"], height=600)

    with right_pane:
        with st.container(border=True):
            st.header("Extracted Information")

            doc_types_labels = list(
                st.session_state.settings["confidence_thresholds"].keys()
            )
            doc_types_values = list(
                st.session_state.settings["confidence_thresholds"].values()
            )
            doc_types = st.session_state.document_types["document_types"]

            current_type = doc_info["predicted_type"]
            current_type_index = (
                doc_types.index(current_type) if current_type in doc_types else 0
            )
            current_type_threshold = doc_types_values[current_type_index]

            selectbox_enable = doc_info["type_confidence"] < current_type_threshold

            with st.expander("Classification Details", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Confidence", f"{doc_info['type_confidence']:.2f}")
                with col2:
                    st.metric("Threshold", f"{current_type_threshold:.2f}")

                if selectbox_enable:
                    new_type_label = st.selectbox(
                        "Correct Document Type",
                        options=doc_types_labels,
                        index=current_type_index,
                    )
                    new_type = doc_types[doc_types_labels.index(new_type_label)]
                    st.info(
                        "Confidence is below threshold. Please review and correct the document type if necessary."
                    )
                else:
                    new_type = doc_info["predicted_type"]
                    st.write(
                        f"**Document Type:** {doc_types_labels[current_type_index]}"
                    )
                    st.warning(
                        "Confidence is above threshold. Document type cannot be changed."
                    )

            st.subheader("Extracted Fields")
            if not doc_info["fields"]:
                st.info("No fields were extracted for this document.")
            else:
                df = pd.DataFrame(doc_info["fields"])
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "value": st.column_config.TextColumn("Value"),
                        "confidence": st.column_config.ProgressColumn(
                            "Confidence",
                            format="%.2f",
                            min_value=0.0,
                            max_value=1.0,
                        ),
                    },
                    disabled=["name", "page", "confidence"],
                    hide_index=True,
                    key=f"editor_{doc_name}",
                )

            if st.button(
                "Save Corrections & Approve",
                use_container_width=True,
                type="primary",
            ):
                with st.spinner("Saving corrections..."):
                    if new_type != doc_info["predicted_type"]:
                        st.session_state.document_classify_review[
                            "classify_reviews"
                        ].append(
                            {
                                "predicted_type": doc_info["predicted_type"],
                                "actual_type": new_type,
                            }
                        )
                        doc_info["predicted_type"] = new_type
                        doc_info["type_confidence"] = 1.0

                    original_df = pd.DataFrame(doc_info["fields"])
                    for _, (edited_row, original_row) in enumerate(
                        zip(
                            edited_df.to_dict("records"), original_df.to_dict("records")
                        )
                    ):
                        if edited_row["value"] != original_row["value"]:
                            facade_loan_system.save_learning_example(
                                doc_type=doc_info["predicted_type"],
                                field_name=edited_row["name"],
                                ai_value=original_row["value"],
                                human_value=edited_row["value"],
                            )

                    predicted_data = {f["name"]: f["value"] for f in doc_info["fields"]}
                    corrected_data = {
                        f["name"]: f["value"] for f in edited_df.to_dict("records")
                    }
                    st.session_state.document_extraction_review[
                        "extraction_reviews"
                    ].append(
                        {
                            "doc_type": doc_info["predicted_type"],
                            "predicted_data": predicted_data,
                            "corrected_data": corrected_data,
                        }
                    )

                    doc_info["fields"] = edited_df.to_dict("records")
                    doc_info["status"] = (
                        "auto_approved" if not selectbox_enable else "needs_review"
                    )
                    st.session_state.documents[doc_name] = doc_info

                    st.success("Corrections saved successfully!")


if __name__ == "__main__":
    document_view_page()
