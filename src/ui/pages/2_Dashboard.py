import altair as alt
import pandas as pd
import streamlit as st
from backend import FacadeLoan


st.set_page_config(layout="wide", page_title="Processing Dashboard")


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def get_metrics():
    classify_reviews = st.session_state.document_classify_review["classify_reviews"]
    extraction_reviews = st.session_state.document_extraction_review[
        "extraction_reviews"
    ]
    ops_metrics = [
        {
            "latency_seconds": data["latency_seconds"],
            "cost_usd": data["cost_usd"],
            "status": data["status"],
        }
        for _, data in st.session_state.documents.items()
    ]
    confident_metrics = [
        {
            "doc_type": data["predicted_type"],
            "confidence": data["type_confidence_original"],
        }
        for _, data in st.session_state.documents.items()
    ]

    classify_metrics, extraction_metrics, ops_metrics_result = (
        FacadeLoan.calculate_metrics(
            classify_reviews,
            extraction_reviews,
            ops_metrics,
        )
    )

    return classify_metrics, extraction_metrics, ops_metrics_result, confident_metrics


def dashboard_page():
    """Page for displaying dashboards and KPIs."""
    local_css("src/ui/styles.css")
    alt.themes.enable("default")
    st.markdown("# Processing Dashboard")

    try:
        classify_metrics, extraction_metrics, ops_metrics_result, confident_metrics = (
            get_metrics()
        )
    except Exception as e:
        st.error(
            f"An error occurred while calculating metrics: {e}. Please ensure there is data to process."
        )
        return

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Tagging Quality",
            "Extraction Quality",
            "Operational Metrics",
            "Confidence Distribution",
        ]
    )

    with tab1:
        with st.container(border=True):
            st.subheader("Classification Performance")
            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Overall Accuracy", f"{classify_metrics.get('accuracy', 0):.2%}"
            )
            col2.metric("Precision", f"{classify_metrics.get('precision', 0):.2%}")
            col3.metric("Recall", f"{classify_metrics.get('recall', 0):.2%}")

        with st.container(border=True):
            st.subheader("Confusion Matrix")
            print(classify_metrics["confusion_matrix"])
            if (
                classify_metrics["confusion_matrix"] is not None
                and classify_metrics["confusion_matrix"].any()
            ):
                cm_df = pd.DataFrame(
                    classify_metrics["confusion_matrix"],
                    columns=classify_metrics["labels"],
                    index=classify_metrics["labels"],
                )
                cm_chart_data = cm_df.stack().reset_index()
                cm_chart_data.columns = ["True Label", "Predicted Label", "Count"]
                heatmap = (
                    alt.Chart(cm_chart_data)
                    .mark_rect(stroke="white", strokeWidth=2)
                    .encode(
                        x="Predicted Label:O",
                        y="True Label:O",
                        color=alt.Color("Count:Q", scale=alt.Scale(scheme="viridis")),
                        tooltip=["True Label", "Predicted Label", "Count"],
                    )
                    .properties(height=400)
                )
                st.altair_chart(heatmap, use_container_width=True)
            else:
                st.info("Not enough data for a confusion matrix.")

    with tab2:
        with st.container(border=True):
            st.subheader("Field-Level Extraction Quality")
            if extraction_metrics:
                df_extraction_metrics = pd.DataFrame(extraction_metrics)
                st.dataframe(
                    df_extraction_metrics,
                    column_config={
                        "exact_match_rate": st.column_config.ProgressColumn(
                            "Exact Match", format="%.2f", min_value=0, max_value=1
                        ),
                        "token_f1_score": st.column_config.ProgressColumn(
                            "Token F1 (Soft Match)",
                            format="%.2f",
                            min_value=0,
                            max_value=1,
                        ),
                    },
                    hide_index=True,
                    use_container_width=True,
                )
                macro_f1 = df_extraction_metrics["token_f1_score"].mean()
                st.metric(
                    "System-wide Extraction Quality (Macro F1)", f"{macro_f1:.1%}"
                )
            else:
                st.info("No extraction metrics available.")

    with tab3:
        with st.container(border=True):
            st.subheader("Latency & Cost")
            ops_col1, ops_col2, ops_col3 = st.columns(3)
            ops_col1.metric(
                "P50 Latency / Doc", f"{ops_metrics_result.get('p50_latency', 0):.2f}s"
            )
            ops_col2.metric(
                "P95 Latency / Doc", f"{ops_metrics_result.get('p95_latency', 0):.2f}s"
            )
            ops_col3.metric(
                "Estimated Cost / Doc",
                f"${ops_metrics_result.get('cost_per_doc', 0):.5f}",
            )

        with st.container(border=True):
            st.subheader("Process Automation")
            ops_col4, ops_col5 = st.columns(2)
            ops_col4.metric(
                "Auto-Approve Rate",
                f"{ops_metrics_result.get('auto_approve_rate', 0):.2%}",
            )
            ops_col5.metric(
                "Human Review Rate",
                f"{ops_metrics_result.get('human_review_rate', 0):.2%}",
            )

    with tab4:
        with st.container(border=True):
            st.subheader("Model Confidence Distribution by Document Type")
            st.caption(
                "Displays the model's 'certainty' levels broken down by document type."
            )
            if confident_metrics:
                df_confident_metrics = pd.DataFrame(confident_metrics)
                df_confident_metrics["confidence"] = df_confident_metrics[
                    "confidence"
                ].clip(0, 1)
                chart = (
                    alt.Chart(df_confident_metrics)
                    .mark_bar()
                    .encode(
                        x=alt.X(
                            "confidence",
                            bin=alt.Bin(step=0.05),
                            title="Confidence Score",
                        ),
                        y=alt.Y("count()", title="Document Count"),
                        color=alt.Color("doc_type", legend=None),
                        tooltip=["doc_type", "count()"],
                    )
                    .properties(height=200)
                    .facet(column=alt.Column("doc_type", title=None))
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No confidence metrics available.")


if __name__ == "__main__":
    dashboard_page()
