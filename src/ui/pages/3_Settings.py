# This file is part of a multi-page Streamlit app.
import streamlit as st

st.set_page_config(layout="centered", page_title="Settings")


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def settings_page():
    """Page for configuring application settings."""
    local_css("src/ui/styles.css")
    st.markdown("# ⚙️ Settings")

    if "settings" not in st.session_state:
        st.error("Session not initialized. Please go back to the main page.")
        if st.button("Go to Main Page"):
            st.switch_page("main.py")
        return

    with st.container(border=True):
        st.subheader("Confidence Thresholds")
        st.markdown(
            "Set the minimum confidence score required for a document type to be "
            "considered a valid prediction. This can help in automatically flagging "
            "low-confidence classifications for manual review."
        )

        thresholds = st.session_state.settings["confidence_thresholds"]

        for doc_type, threshold in thresholds.items():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{doc_type}**")
            with col2:
                new_threshold = st.slider(
                    f"Threshold for {doc_type}",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(threshold),
                    step=0.05,
                    key=f"slider_{doc_type}",
                    label_visibility="collapsed",
                )
                st.session_state.settings["confidence_thresholds"][doc_type] = (
                    new_threshold
                )

    st.divider()

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        if st.button("💾 Save Settings", use_container_width=True, type="primary"):
            # In a real app, you might save this to a user profile or a config file
            with st.spinner("Saving..."):
                import time

                time.sleep(1)
                st.success("✅ Settings saved successfully!")

    # Display current settings for verification
    with st.expander("Show Current Threshold Values"):
        st.json(st.session_state.settings["confidence_thresholds"])


if __name__ == "__main__":
    settings_page()
