"""Streamlit web interface for BioProof."""

import streamlit as st
import os
import json
import tempfile
from bioproof.analyzer import analyze_image

st.set_page_config(page_title="BioProof", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .big-title {
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        margin-bottom: 1rem !important;
    }
    .upload-text {
        font-size: 1.5rem !important;
        margin-bottom: 2rem !important;
    }
    .result-card {
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
        border-left: 6px solid;
        background: rgba(255,255,255,0.05);
    }
    .result-filename {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
    }
    .result-status {
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        margin: 0.3rem 0;
    }
    .result-reason {
        font-size: 1.1rem !important;
        opacity: 0.9;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">BioProof</h1>', unsafe_allow_html=True)
st.markdown('<p class="upload-text">Scientific Image Integrity Verification</p>', unsafe_allow_html=True)

# Quick guide
with st.expander("How does this work?"):
    st.markdown("""
    **PASS** — Image appears authentic. Has camera/device data confirming it came from real lab equipment. No synthetic patterns detected. OR synthetic generation was properly declared with valid watermark.

    **NEEDS REVIEW** — Suspicious patterns detected (possible digital generation or manipulation), but has source verification. Human expert should inspect.

    **POLICY ISSUE** — High risk of digital generation. No device data to prove origin, and/or synthetic patterns detected. Cannot verify as authentic.

    ---

    **Digital Generation Declaration:**
    - **Yes** — You confirm digital tools were used. Image must have a watermark (metadata or visible stamp) to pass.
    - **No** — You confirm no digital tools were used. Image will be analyzed for authenticity.
    - **Unsure** — Not sure if digital tools were used. Image will be analyzed normally (treated as "No").
    """)

# File uploader
uploads = st.file_uploader(
    "Drop 1 to 10 images",
    type=["tif", "tiff", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

# Initialize session state for digital generation declarations
if 'digital_declarations' not in st.session_state:
    st.session_state.digital_declarations = {}
if 'results' not in st.session_state:
    st.session_state.results = []

if uploads:
    st.markdown("---")
    st.subheader("Configure Each Image")

    # Display radio buttons for each file
    for f in uploads:
        col1, col2 = st.columns([2, 2])
        with col1:
            st.write(f"**{f.name}**")
        with col2:
            digital_used = st.radio(
                "Did you use digital tools to generate this image?",
                options=["No", "Unsure", "Yes"],
                key=f"digital_radio_{f.name}",
                horizontal=True,
                index=0
            )
            st.session_state.digital_declarations[f.name] = (digital_used == "Yes")

    st.markdown("---")

    # Run checks button
    if st.button("Run Checks", type="primary", use_container_width=True):
        st.session_state.results = []

        with st.spinner("Analyzing images..."):
            with tempfile.TemporaryDirectory() as tmp:
                for f in uploads:
                    # Save uploaded file to temp directory
                    path = os.path.join(tmp, f.name)
                    with open(path, "wb") as out:
                        out.write(f.getbuffer())

                    # Get digital generation declaration for this file
                    digital_declared = st.session_state.digital_declarations.get(f.name, False)

                    # Analyze the image
                    res = analyze_image(path, ai_declared=digital_declared)
                    st.session_state.results.append(res)

        st.success("Analysis complete!")

# Display results
if st.session_state.results:
    st.markdown("---")
    st.subheader("Results")

    for r in st.session_state.results:
        status = r["status"]

        # Define colors based on status
        if status == "Pass":
            color = "#2ba84a"
            border_color = "#2ba84a"
        elif status == "Needs review":
            color = "#f0ad4e"
            border_color = "#f0ad4e"
        else:  # Policy issue
            color = "#d9534f"
            border_color = "#d9534f"

        # Display result card
        st.markdown(f"""
        <div class="result-card" style="border-left-color: {border_color};">
            <div class="result-filename">{r['file']}</div>
            <div class="result-status" style="color: {color};">{status.upper()}</div>
            <div class="result-reason">{r['reason']}</div>
        </div>
        """, unsafe_allow_html=True)
