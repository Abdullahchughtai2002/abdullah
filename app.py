import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from PyPDF2 import PdfReader
import docx

# Load API Key
groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
if not groq_api_key:
    st.error("❌ GROQ_API_KEY not set. Please set it before running.")
    st.stop()

# Styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #f7f9fc, #eef2f7);
        font-family: 'Segoe UI', sans-serif;
    }
    .app-title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: purple;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: purple;
        margin-bottom: 30px;
    }
    .stTextArea textarea {
        border-radius: 10px !important;
    }
    .stButton>button {
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Init LLM
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_api_key)

# Sidebar
st.sidebar.title("Settings")
creativity = st.sidebar.slider("Creativity", 0, 100, 50)
personalization = st.sidebar.slider("Personalization", 0, 100, 70)
st.sidebar.caption("Built by *Abdullah Chughtai* 😉")

# Title
st.markdown('<div class="app-title">AI Job Application Helper ✨</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Smart, personalized job emails — powered by Groq + LangChain</div>', unsafe_allow_html=True)

# Upload & Manual Inputs
col_job, col_portfolio = st.columns(2)
with col_job:
    job_description = st.text_area("📄 Paste Job Description")
with col_portfolio:
    uploaded_resume = st.file_uploader("📎 Upload Resume (PDF/DOCX)", type=["pdf", "docx"])
    portfolio = ""
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
        st.success("Resume text extracted ✅")
    if not portfolio:
        portfolio = st.text_area("Or Paste Portfolio / Resume here:")

# JD Summarizer in expander
with st.expander("🔎 Summarize Job Description (Optional)"):
    if job_description.strip() and st.button("Summarize JD"):
        summarize_prompt = PromptTemplate(
            input_variables=["job_description"],
            template="Summarize the following job description in 3-4 bullet points:\n\n{job_description}"
        )
        jd_summary = LLMChain(llm=llm, prompt=summarize_prompt).run({"job_description": job_description})
        st.markdown("#### JD Summary")
        st.write(jd_summary)

# Email Customization in columns
st.subheader("⚙️ Email Customization")
col1, col2 = st.columns(2)
with col1:
    tone = st.selectbox("Tone", ["Professional", "Friendly", "Persuasive", "Concise"])
with col2:
    email_format = st.selectbox("Format", ["Formal Letter", "Short Note"])

# Session State
if "email_history" not in st.session_state:
    st.session_state.email_history = []

# Generate Email
if st.button("🚀 Generate Email"):
    if job_description and portfolio:
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
        response = LLMChain(llm=llm, prompt=prompt).run({
            "job_description": job_description,
            "portfolio": portfolio,
            "tone": tone,
            "creativity": creativity,
            "personalization": personalization,
            "email_format": email_format
        })

        subject_prompt = PromptTemplate(
            input_variables=["job_description"],
            template="Write a catchy subject line for a cold email based on this job description:\n{job_description}"
        )
        subject_line = LLMChain(llm=llm, prompt=subject_prompt).run({"job_description": job_description})

        st.subheader("📌 Subject Line")
        st.write(subject_line)
        st.subheader("✉ Email")
        st.write(response)

        st.download_button(
            "📥 Download Email",
            data=f"Subject: {subject_line}\n\n{response}",
            file_name="cold_email.txt",
            mime="text/plain"
        )

        st.session_state.email_history.append({"subject": subject_line, "body": response})
    else:
        st.warning("⚠ Please provide both Job Description and Portfolio.")

# History
if st.session_state.email_history:
    st.subheader("📜 Previous Emails")
    for i, email in enumerate(st.session_state.email_history):
        with st.expander(f"{i+1}. {email['subject']}"):
            st.write(email['body'])
