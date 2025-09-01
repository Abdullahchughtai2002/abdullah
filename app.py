import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from PyPDF2 import PdfReader
import docx

# Load API Key from secrets or environment variable
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key and "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]

if not groq_api_key:
    st.error("❌ GROQ_API_KEY not set. Please set it before running.")
    st.stop()

# CSS for Styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #ffffff, #f0f4f8);
        font-family: 'Poppins', sans-serif;
        color: black;
    }
    .title {
        text-align: center;
        font-size: 42px;
        font-weight: bold;
        color: Yellow; /* Dark Bold Color */
        margin-bottom: 20px;
    }
    .stTextArea textarea {
        background-color: #f9f9f9 !important;
        color: black !important;
        border: 1px solid #ddd !important;
        border-radius: 12px;
        padding: 10px;
        font-size: 16px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1e3d59, #3a6ea5);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 28px;
        font-size: 18px;
        font-weight: bold;
        transition: 0.3s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #3a6ea5, #1e3d59);
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_api_key)

# Sidebar Settings
st.sidebar.markdown("## Abdullah's Portfolio")
creativity = st.sidebar.slider("Creativity", 0, 100, 50)
personalization = st.sidebar.slider("Personalization", 0, 100, 70)
st.sidebar.markdown("---")
st.sidebar.caption("Developed by *Abdullah Chughtai*")

# Main Title
st.markdown('<div class="title">📧 AI Cold Email Generator</div>', unsafe_allow_html=True)
st.write("Generate *personalized* job application emails using *Groq + LangChain + Streamlit*.")

# Upload Resume & Extract Text
portfolio = ""
uploaded_resume = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])

if uploaded_resume:
    if uploaded_resume.type == "application/pdf":
        reader = PdfReader(uploaded_resume)
        extracted_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif uploaded_resume.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_resume)
        extracted_text = "\n".join([para.text for para in doc.paragraphs])
    else:
        extracted_text = ""
    portfolio = extracted_text
    st.success("Resume text extracted successfully!")

# Manual Inputs
job_description = st.text_area("Paste Job Description here:")
if not portfolio:
    portfolio = st.text_area("Paste Portfolio / Resume here:")

# --- NEW FEATURE: Job Description Summarizer ---
st.subheader("📝 Optional: Summarize Job Description")
if job_description.strip():
    if st.button("Summarize JD"):
        summarize_prompt = PromptTemplate(
            input_variables=["job_description"],
            template=(
                "Summarize the following job description in 3-4 bullet points, "
                "highlighting key responsibilities, required skills, and any important notes:\n\n"
                "{job_description}"
            ),
        )
        summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)
        jd_summary = summarize_chain.run({"job_description": job_description})
        st.markdown("### 📄 JD Summary")
        st.write(jd_summary)

# Email Tone & Format
st.subheader("⚒ Email Customization")
tone = st.radio("Choose the tone:", ["Professional", "Friendly", "Persuasive", "Concise"], index=0, horizontal=True)
email_format = st.radio("Choose Email Format:", ["Formal Letter", "Short Note"], index=0, horizontal=True)

# Session State for History
if "email_history" not in st.session_state:
    st.session_state.email_history = []

# Generate Email Button
if st.button("Generate Email"):
    if job_description and portfolio:
        # Email Body Prompt
        prompt = PromptTemplate(
            input_variables=["job_description", "portfolio", "tone", "creativity", "personalization", "email_format"],
            template=(
                "You are an assistant drafting a {tone} cold email in {email_format} style.\n"
                "Creativity Level: {creativity}/100.\n"
                "Personalization Level: {personalization}/100.\n\n"
                "Job Description:\n{job_description}\n\n"
                "Portfolio/Resume:\n{portfolio}\n\n"
                "Write a cold email tailored for this job."
            ),
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        response = chain.run({
            "job_description": job_description,
            "portfolio": portfolio,
            "tone": tone,
            "creativity": creativity,
            "personalization": personalization,
            "email_format": email_format
        })

        # Subject Line Generator
        subject_prompt = PromptTemplate(
            input_variables=["job_description"],
            template="Write a catchy subject line for a cold email based on this job description:\n{job_description}"
        )
        subject_chain = LLMChain(llm=llm, prompt=subject_prompt)
        subject_line = subject_chain.run({"job_description": job_description})

        # Display Output
        st.subheader("📌 Suggested Subject Line")
        st.write(f"{subject_line}")

        st.subheader("✉ Generated Cold Email")
        st.write(response)

        # Download Button
        email_text = f"Subject: {subject_line}\n\n{response}"
        st.download_button(
            label="📥 Download Email as TXT",
            data=email_text,
            file_name="cold_email.txt",
            mime="text/plain"
        )

        # Save to History
        st.session_state.email_history.append({"subject": subject_line, "body": response})
    else:
        st.warning("⚠ Please provide both Job Description and Portfolio.")

# Show History
if st.session_state.email_history:
    st.subheader("📜 Email History")
    for idx, email in enumerate(st.session_state.email_history):
        with st.expander(f"Email {idx+1}: {email['subject']}"):
            st.write(email['body'])
