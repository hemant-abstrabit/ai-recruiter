import streamlit as st
import json
import os
from dotenv import load_dotenv
from criteria_generator import CriteriaGenerator
load_dotenv()

def main():
    st.set_page_config(
        page_title="AI Recruiter - Selection Criteria Generator",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 AI Recruiter System")
    st.subheader("Selection Criteria Generator")
    
    # Initialize session state
    if 'criteria_generated' not in st.session_state:
        st.session_state.criteria_generated = False
    if 'generated_criteria' not in st.session_state:
        st.session_state.generated_criteria = []
    
    # Check if API key is available in environment
    env_key_available = bool(os.getenv('GEMINI_API_KEY'))
    
    if not env_key_available:
        st.error("⚠️ GEMINI_API_KEY environment variable not set. Please set it before running the app.")
        st.stop()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Input")
        
        # Job Role input
        job_role = st.text_input(
            "Job Role",
            placeholder="e.g., Senior Software Engineer, Data Scientist, Product Manager",
            help="Enter the job role/title for which you want to generate selection criteria"
        )
        
        # Job Description input
        jd_text = st.text_area(
            "Job Description",
            placeholder="Paste the job description here...",
            height=300,
            help="Enter the complete job description for which you want to generate selection criteria"
        )
        
        # Additional instructions
        user_guidance = st.text_area(
            "Additional Instructions (Optional)",
            placeholder="Any specific requirements or focus areas...",
            height=100,
            help="Optional: Provide any additional context or specific requirements"
        )
        
        # Generate button
        if st.button("Generate Selection Criteria", type="primary"):
            if not job_role.strip():
                st.error("Please enter a job role")
            elif not jd_text.strip():
                st.error("Please enter a job description")
            else:
                generate_criteria(job_role, jd_text, user_guidance)
    
    with col2:
        st.header("Generated Selection Criteria")
        
        if st.session_state.criteria_generated:
            display_criteria()
        else:
            st.info("Enter job role and description, then click 'Generate Selection Criteria' to see results")


def generate_criteria(job_role: str, jd_text: str, user_guidance: str):
    """Generate selection criteria using the CriteriaGenerator."""
    with st.spinner("Generating selection criteria..."):
        try:
            generator = CriteriaGenerator()  # Will use environment API key
            criteria = generator.generate_criteria(job_role, jd_text, user_guidance)
            
            st.session_state.generated_criteria = criteria
            st.session_state.criteria_generated = True
            
            st.success(f"Successfully generated {len(criteria)} selection criteria!")
            
        except ValueError as e:
            st.error(f"Validation Error: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")


def display_criteria():
    """Display the generated criteria in a formatted way."""
    criteria = st.session_state.generated_criteria
    
    if not criteria:
        st.warning("No criteria to display")
        return
    
    # Summary metrics
    total_weight = sum(float(c['weight'][:-1]) for c in criteria)
    must_have_count = sum(1 for c in criteria if c['must_have'] == 'Yes')
    
    # Display metrics
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Total Criteria", len(criteria))
    with metric_col2:
        st.metric("Must-Have Items", must_have_count)
    with metric_col3:
        st.metric("Total Weight", f"{total_weight:.1f}%")
    
    st.divider()
    
    # Display criteria
    for i, criterion in enumerate(criteria, 1):
        with st.expander(f"{i}. {criterion['name']} ({criterion['weight']})", expanded=True):
            col_left, col_right = st.columns([1, 3])
            
            with col_left:
                if criterion['must_have'] == 'Yes':
                    st.error("🔴 Must-Have")
                else:
                    st.info("🔵 Nice-to-Have")
                st.write(f"**Weight:** {criterion['weight']}")
            
            with col_right:
                st.write("**Description:**")
                st.write(criterion['description'])
    
    st.divider()
    
    # Download options
    st.subheader("Export Options")
    
    col_download1, col_download2 = st.columns(2)
    
    with col_download1:
        # JSON download
        json_data = json.dumps(criteria, indent=2)
        st.download_button(
            label="Download as JSON",
            data=json_data,
            file_name="selection_criteria.json",
            mime="application/json"
        )
    
    with col_download2:
        # Formatted text download
        generator = CriteriaGenerator()  # Will use env key for display formatting
        formatted_text = generator.format_criteria_for_display(criteria)
        st.download_button(
            label="Download as Text",
            data=formatted_text,
            file_name="selection_criteria.txt",
            mime="text/plain"
        )


if __name__ == "__main__":
    main()