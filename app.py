"""
app.py - Streamlit Frontend for Document Brochure Generator
Simplified version that works reliably with Streamlit
"""

import streamlit as st
import json
import sys
from pathlib import Path

# Import processing scripts
from ingest import run_ingest
from summarizer import run_summarizer

# Page config
st.set_page_config(
    page_title="Document Brochure Generator",
    page_icon="📄",
    layout="wide"
)

# Directories
DATA_DOCS_DIR = Path("./data/docs")
DATA_IMAGES_DIR = Path("./data/images")
JOBS_DIR = Path("./jobs")

# Create directories
DATA_DOCS_DIR.mkdir(parents=True, exist_ok=True)
DATA_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)


def clear_docs_folder():
    """Clear all files in data/docs."""
    if DATA_DOCS_DIR.exists():
        for file in DATA_DOCS_DIR.iterdir():
            if file.is_file():
                file.unlink()
        return True
    return False


def save_uploaded_files(uploaded_files):
    """Save uploaded files to data/docs."""
    saved_files = []
    for uploaded_file in uploaded_files:
        file_path = DATA_DOCS_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_files.append(uploaded_file.name)
    return saved_files


def load_brochure(job_id):
    """Load brochure JSON from job directory."""
    brochure_path = JOBS_DIR / job_id / "brochure.json"
    if brochure_path.exists():
        with open(brochure_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def display_brochure(brochure):
    """Display brochure in beautiful format."""
    
    st.markdown("---")
    st.markdown(f"# 📄 {brochure.get('title', 'N/A')}")
    st.markdown(f"### *{brochure.get('subtitle', 'N/A')}*")
    st.markdown("---")
    
    st.markdown("## 📋 Introduction")
    st.info(brochure.get('intro_summary', 'N/A'))
    
    st.markdown("## ✨ Key Features")
    features = brochure.get('key_features', [])
    if features:
        cols = st.columns(2)
        for idx, feature in enumerate(features):
            with cols[idx % 2]:
                st.markdown(f"**🔹 {feature.get('feature', 'N/A')}**")
                st.write(feature.get('description', 'N/A'))
                st.markdown("")
    else:
        st.warning("No features available")
    
    st.markdown("## 🏆 Competitive Advantages")
    advantages = brochure.get('competitive_advantages', [])
    if advantages:
        for adv in advantages:
            st.success(f"**💡 {adv.get('advantage', 'N/A')}**")
            st.write(adv.get('explanation', 'N/A'))
    else:
        st.warning("No advantages available")
    
    st.markdown("## ⚙️ How It Works")
    steps = brochure.get('how_it_works', [])
    if steps:
        for step in steps:
            step_num = step.get('step', 0)
            st.markdown(f"### Step {step_num}: {step.get('title', 'N/A')}")
            st.write(step.get('description', 'N/A'))
            st.markdown("")
    else:
        st.warning("No workflow steps available")
    
    st.markdown("## 💭 Additional Insights")
    st.write(brochure.get('additional_insights', 'N/A'))
    
    metadata = brochure.get('_metadata', {})
    if metadata:
        st.markdown("---")
        with st.expander("📊 Generation Metadata"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Model", metadata.get('model', 'N/A'))
            with col2:
                st.metric("Chunks Processed", metadata.get('n_chunks_processed', 'N/A'))
            with col3:
                st.metric("Total Tokens", metadata.get('total_tokens', 'N/A'))


def main():
    st.title("📄 Document Brochure Generator")
    st.markdown("Upload PDF/DOCX files and generate professional brochures automatically!")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        st.info(f"🐍 Python: `{sys.version.split()[0]}`")
        st.info(f"📂 Dir: `{Path.cwd().name}`")
        
        clear_previous = st.checkbox("Clear previous files before upload", value=True)
        
        st.markdown("---")
        st.markdown("### 📁 Files in data/docs/")
        existing_files = list(DATA_DOCS_DIR.glob("*.pdf")) + list(DATA_DOCS_DIR.glob("*.docx"))
        if existing_files:
            for f in existing_files:
                st.text(f"• {f.name}")
        else:
            st.info("No files")
        
        if st.button("🗑️ Clear All Files", type="secondary"):
            if clear_docs_folder():
                st.success("Files cleared!")
                st.rerun()
    
    # Main tabs
    tab1, tab2 = st.tabs(["📤 Upload & Generate", "📂 Previous Jobs"])
    
    with tab1:
        st.header("Step 1: Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Upload PDF or DOCX files",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Select one or more files"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")
            for file in uploaded_files:
                st.text(f"• {file.name}")
            
            if st.button("💾 Start Processing", type="primary", use_container_width=True):
                
                # Clear previous files if needed
                if clear_previous:
                    clear_docs_folder()
                    st.info("✅ Previous files cleared")
                
                # Save files
                saved_files = save_uploaded_files(uploaded_files)
                st.success(f"✅ Saved {len(saved_files)} file(s)")
                
                # Step 2: Ingest
                st.markdown("---")
                st.header("Step 2: Document Ingestion")
                
                progress_text = st.empty()
                progress_text.info("🔄 Running ingestion pipeline...")
                
                try:
                    result = run_ingest()
                    job_id = result.get("job_id")
                    progress_text.success(f"✅ Ingestion complete! Job ID: `{job_id}`")
                    
                    # Show result details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Files Processed", len(saved_files))
                    with col2:
                        st.metric("Chunks Created", result.get('n_chunks', 0))
                    with col3:
                        st.metric("Job ID", job_id[:8] + "...")
                    
                    # Step 3: Summarizer
                    st.markdown("---")
                    st.header("Step 3: Brochure Generation")
                    
                    sum_progress = st.empty()
                    sum_progress.info("🔄 Generating brochure with AI...")
                    
                    try:
                        sum_result = run_summarizer(job_id=job_id)
                        sum_progress.success("✅ Brochure generated!")
                        
                        # Step 4: Display
                        st.markdown("---")
                        st.header("Step 4: Generated Brochure")
                        
                        brochure = load_brochure(job_id)
                        if brochure:
                            display_brochure(brochure)
                            
                            # Download button
                            st.markdown("---")
                            brochure_json = json.dumps(brochure, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="📥 Download Brochure JSON",
                                data=brochure_json,
                                file_name=f"brochure_{job_id}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        else:
                            st.error(f"❌ Could not load brochure file")
                            st.error(f"Expected at: `{JOBS_DIR / job_id / 'brochure.json'}`")
                            
                    except Exception as e:
                        sum_progress.error("❌ Summarizer failed!")
                        st.error(f"Error: {str(e)}")
                        with st.expander("🔍 Error Details"):
                            st.code(str(e))
                        
                except Exception as e:
                    progress_text.error("❌ Ingestion failed!")
                    st.error(f"Error: {str(e)}")
                    with st.expander("🔍 Error Details"):
                        st.code(str(e))
    
    with tab2:
        st.header("📂 Previous Jobs")
        
        if not JOBS_DIR.exists() or not list(JOBS_DIR.iterdir()):
            st.info("No previous jobs found")
        else:
            job_dirs = sorted(
                [d for d in JOBS_DIR.iterdir() if d.is_dir()], 
                key=lambda x: x.name, 
                reverse=True
            )
            
            if not job_dirs:
                st.info("No previous jobs found")
            else:
                job_options = [d.name for d in job_dirs]
                selected_job = st.selectbox("Select a job to view", job_options)
                
                if selected_job:
                    brochure = load_brochure(selected_job)
                    if brochure:
                        display_brochure(brochure)
                        
                        st.markdown("---")
                        brochure_json = json.dumps(brochure, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download Brochure JSON",
                            data=brochure_json,
                            file_name=f"brochure_{selected_job}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    else:
                        st.warning("No brochure found for this job")
                        job_dir = JOBS_DIR / selected_job
                        st.markdown("### Job Directory Contents:")
                        for item in job_dir.iterdir():
                            st.text(f"• {item.name}")


if __name__ == "__main__":
    main()