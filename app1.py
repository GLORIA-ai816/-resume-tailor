# CareerLens – Resume Tailor & Job Match Coach
# Requirements: streamlit openai PyPDF2 fpdf plotly
# pip install streamlit openai PyPDF2 fpdf plotly

import streamlit as st
import openai
import json
import re
import io
from fpdf import FPDF
import plotly.graph_objects as go

API_MODEL = "glm-4-flash"
API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
API_KEY_NAME = "ZHIPUAI_API_KEY"

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CareerLens",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  .stApp {
    background: linear-gradient(135deg, #fdf6ec 0%, #eef4fb 50%, #e8f5f2 100%);
  }
  .glass-card {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.55);
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
    padding: 1.6rem 2rem;
    margin-bottom: 1.2rem;
    transition: box-shadow 0.25s ease;
  }
  .glass-card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.12); }
  .score-label { font-size: 2.6rem; font-weight: 700; text-align: center; }
  .badge-green {
    display:inline-block; background:#d1fae5; color:#065f46;
    border-radius:999px; padding:3px 14px;
    font-size:0.82rem; font-weight:600; margin: 3px 4px;
  }
  .badge-amber {
    display:inline-block; background:#fef3c7; color:#92400e;
    border-radius:999px; padding:3px 14px;
    font-size:0.82rem; font-weight:600; margin: 3px 4px;
  }
  .onboarding-banner {
    background: linear-gradient(90deg,#6366f1,#06b6d4);
    color:white; border-radius:14px; padding:14px 22px;
    font-size:1rem; font-weight:500; margin-bottom:1.2rem;
    display:flex; align-items:center; gap:12px;
  }
  .thinking {
    background: linear-gradient(90deg,#f0fdf4,#ecfeff);
    border-left: 4px solid #34d399; border-radius: 8px;
    padding: 14px 18px; font-style: italic;
    color: #065f46; margin: 1rem 0;
  }
  .privacy-note {
    font-size:0.78rem; color:#6b7280;
    display:flex; align-items:center; gap:6px; margin-top: 0.5rem;
  }
  .soft-warn {
    background:#fffbeb; border-left: 3px solid #fbbf24;
    border-radius: 6px; padding: 8px 14px;
    font-size:0.88rem; color:#92400e; margin-top: 6px;
  }
  .css-1d391kg { padding-top: 1rem; }
  button[data-baseweb="tab"] {
    font-size: 0.95rem !important; font-weight: 600 !important;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_openai_client():
    try:
        api_key = st.secrets["ZHIPUAI_API_KEY"]
    except Exception:
        return None, "missing_key"
    return openai.OpenAI(api_key=api_key, base_url=API_BASE_URL), None


def extract_pdf_text(uploaded_file) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def resume_health_check(resume_text: str) -> list[str]:
    hints = []
    low = resume_text.lower()
    if not re.search(r"[\w.+-]+@[\w-]+\.\w+", resume_text):
        hints.append("Looks like an email address is missing — recruiters need a way to reach you.")
    if not re.search(r"\d{3}[\s\-.]?\d{3}[\s\-.]?\d{4}", resume_text):
        hints.append("Consider adding a phone number for a complete contact section.")
    if "linkedin" not in low and "github" not in low:
        hints.append("A LinkedIn or GitHub URL can strengthen first impressions.")
    if len(resume_text.split()) < 150:
        hints.append("Your resume feels brief — a bit more detail about your experience can help.")
    if "objective" in low or "references available" in low:
        hints.append("Objective statements & 'references available' are outdated — consider removing them.")
    return hints


def build_system_prompt(style: str, gen_cover: bool, gen_interview: bool) -> str:
    style_notes = {
        "Modern & Warm": "Use a warm, approachable tone with active verbs and relatable language.",
        "Professional": "Use a formal, concise, executive tone — no fluff.",
        "Academic": "Use precise language, emphasise projects, research, and methodologies if present.",
    }
    extras = []
    if gen_cover:
        extras.append(
            '"cover_letter": a tailored cover letter (3-4 paragraphs, <300 words) '
            'that merges the resume\'s voice with the job description\'s tone.'
        )
    if gen_interview:
        extras.append(
            '"interview_questions": a list of exactly 5 likely interview questions for this role, '
            'each as an object with "question" (string) and "answer" (string, concise model answer, 2-4 sentences).'
        )

    extra_fields = ("\n" + "\n".join(f"      - {e}" for e in extras)) if extras else ""

    return f"""You are an expert career coach and resume specialist. {style_notes.get(style, '')}

Your task:
1. Read the candidate's resume and the job description carefully.
2. Produce a tailored version of the resume that:
   - Emphasises keywords and achievements that match the JD.
   - Never fabricates experience or skills.
   - Returns the tailored resume in clean, well-structured Markdown.
3. Also produce a JSON analytics block.

IMPORTANT – your response must follow this EXACT format (nothing before or after):

TAILORED_RESUME_START
<the tailored resume in Markdown here>
TAILORED_RESUME_END

ANALYTICS_START
{{
  "match_score": <integer 0-100>,
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "missing_skills": ["<skill 1>", "<skill 2>", "<skill 3>"],
  "learning_path": [
    {{"skill": "<skill>", "resources": ["<free resource or course name + URL>", "<resource 2>"]}},
    {{"skill": "<skill>", "resources": ["<free resource or course name + URL>", "<resource 2>"]}}
  ],
  "summary": "<2-sentence encouraging explanation of fit>"{"," if extras else ""}
  {extra_fields.strip()}
}}
ANALYTICS_END"""


def call_openai(client, model: str, resume: str, jd: str, system_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=API_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"RESUME:\n{resume}\n\n---\n\nJOB DESCRIPTION:\n{jd}"},
            ],
            max_tokens=4096,
            temperature=0.4,
        )
        return response.choices[0].message.content
    except openai.RateLimitError:
        return "RATE_LIMIT"
    except openai.AuthenticationError:
        return "AUTH_ERROR"
    except Exception as e:
        return f"ERROR:{e}"


def parse_response(raw: str):
    resume_match = re.search(
        r"TAILORED_RESUME_START\s*(.*?)\s*TAILORED_RESUME_END", raw, re.DOTALL
    )
    analytics_match = re.search(
        r"ANALYTICS_START\s*(.*?)\s*ANALYTICS_END", raw, re.DOTALL
    )
    tailored = resume_match.group(1).strip() if resume_match else raw.strip()
    analytics = {}
    if analytics_match:
        try:
            analytics = json.loads(analytics_match.group(1).strip())
        except json.JSONDecodeError:
            analytics = {}
    return tailored, analytics


def make_resume_pdf(tailored_resume: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Helvetica", size=11)
    for line in tailored_resume.split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(4)
            continue
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, line[2:], ln=True)
            pdf.set_font("Helvetica", size=11)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, line[3:], ln=True)
            pdf.set_font("Helvetica", size=11)
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 7, line[4:], ln=True)
            pdf.set_font("Helvetica", size=11)
        elif line.startswith("- ") or line.startswith("* "):
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", line[2:])
            pdf.cell(5, 6, "", ln=False)
            pdf.multi_cell(0, 6, f"• {clean}")
        else:
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
            pdf.multi_cell(0, 6, clean)
    return bytes(pdf.output())


def make_questions_pdf(questions: list) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "Interview Preparation – CareerLens", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.ln(2)
    for i, q in enumerate(questions, 1):
        question = q.get("question", "") if isinstance(q, dict) else str(q)
        answer = q.get("answer", "") if isinstance(q, dict) else ""
        pdf.set_font("Helvetica", "B", 12)
        pdf.multi_cell(0, 7, f"Q{i}: {question}")
        if answer:
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 6, f"A: {answer}")
        pdf.ln(4)
    return bytes(pdf.output())


def make_cover_pdf(cover_letter: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(22, 22, 22)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Cover Letter – CareerLens", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.ln(3)
    for para in cover_letter.split("\n\n"):
        pdf.multi_cell(0, 6, para.strip())
        pdf.ln(4)
    return bytes(pdf.output())


def score_color(score: int):
    if score >= 75:
        return "#10b981", "#d1fae5"
    elif score >= 50:
        return "#f59e0b", "#fef3c7"
    else:
        return "#f97316", "#ffedd5"


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/telescope.png", width=56)
    st.markdown("## CareerLens ⚙️")
    st.caption("Your personal AI career coach")
    st.divider()

    resume_style = st.selectbox(
        "Resume Style",
        ["Modern & Warm", "Professional", "Academic"],
    )
    gen_cover = st.toggle("Generate Cover Letter", value=True)
    gen_interview = st.toggle("Generate Interview Questions", value=True)

    model_choice = st.selectbox(
        "AI Model",
        [API_MODEL],
        help="使用智谱AI GLM 模型进行分析。",
    )

    st.divider()

    if st.button("🗑️ Start Fresh", use_container_width=True):
        st.warning("This will clear all inputs and results. Click again to confirm.")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown(
        '<div class="privacy-note">🔒 Your data is processed once and never stored. '
        'We respect your privacy.</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# Main area
# ─────────────────────────────────────────────

if "onboarding_dismissed" not in st.session_state:
    st.markdown(
        '<div class="onboarding-banner">🎯 <span><strong>Welcome to CareerLens!</strong> '
        'Paste your resume and a job you love, and our AI coach will do the rest.</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("✕ Dismiss", key="dismiss_onboarding"):
        st.session_state["onboarding_dismissed"] = True
        st.rerun()

client, key_error = get_openai_client()
if key_error == "missing_key":
    st.error(
        "**智谱AI API Key 未找到。**\n\n"
        "请将 Key 添加到 Streamlit Secrets：\n"
        "1. 创建 `.streamlit/secrets.toml` 文件\n"
        "2. 添加：`ZHIPUAI_API_KEY = \"your-key-here\"`\n\n"
        "[→ 前往智谱AI获取Key](https://open.bigmodel.cn/usercenter/apikeys)"
    )
    st.stop()

# ─── Inputs ───────────────────────────────────
st.markdown("## 📄 Your Resume & Job Description")

col_resume, col_jd = st.columns(2, gap="large")

with col_resume:
    st.markdown("### Your Resume")
    uploaded = st.file_uploader(
        "Upload resume (.txt or .pdf)", type=["txt", "pdf"], label_visibility="collapsed"
    )
    resume_text = ""
    if uploaded:
        if uploaded.type == "application/pdf":
            resume_text = extract_pdf_text(uploaded)
        else:
            resume_text = uploaded.read().decode("utf-8", errors="ignore")

    resume_input = st.text_area(
        "Or paste your resume here",
        value=resume_text,
        height=340,
        placeholder="Paste your full resume text here…",
        label_visibility="collapsed",
    )

    if resume_input.strip():
        hints = resume_health_check(resume_input)
        if hints:
            with st.expander("💡 Resume health check", expanded=True):
                for h in hints:
                    st.markdown(f'<div class="soft-warn">💡 {h}</div>', unsafe_allow_html=True)

with col_jd:
    st.markdown("### Job Description")
    jd_input = st.text_area(
        "Paste the job description here",
        height=380,
        placeholder="Paste the full job posting here…",
        label_visibility="collapsed",
    )

st.markdown("<br>", unsafe_allow_html=True)

run_col, _ = st.columns([1, 3])
with run_col:
    analyze_clicked = st.button(
        "🔍 Analyze & Tailor My Resume",
        type="primary",
        use_container_width=True,
    )

if analyze_clicked:
    missing = []
    if not resume_input.strip():
        missing.append("resume")
    if not jd_input.strip():
        missing.append("job description")
    if missing:
        st.markdown(
            f'<div class="soft-warn">Please add your {" and ".join(missing)} before analyzing.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="thinking">✨ Our AI coach is crafting your personalized resume… '
            'This usually takes 15–30 seconds.</div>',
            unsafe_allow_html=True,
        )
        with st.spinner(""):
            system_prompt = build_system_prompt(resume_style, gen_cover, gen_interview)
            raw = call_openai(client, model_choice, resume_input, jd_input, system_prompt)

        if raw == "RATE_LIMIT":
            st.warning("⏳ Too many requests — please wait a moment and try again.")
        elif raw == "AUTH_ERROR":
            st.error("认证失败，请检查 `ZHIPUAI_API_KEY` 是否正确。")
        elif raw.startswith("ERROR:"):
            st.error(f"Something went wrong: {raw[6:]}")
        else:
            tailored, analytics = parse_response(raw)
            st.session_state["tailored"] = tailored
            st.session_state["analytics"] = analytics
            st.session_state["gen_cover"] = gen_cover
            st.session_state["gen_interview"] = gen_interview
            st.rerun()

# ─────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────
if "tailored" in st.session_state:
    tailored: str = st.session_state["tailored"]
    analytics: dict = st.session_state["analytics"]
    did_cover = st.session_state.get("gen_cover", False)
    did_interview = st.session_state.get("gen_interview", False)

    st.markdown("---")
    st.markdown("## 🎉 Your Results")

    tab_labels = ["✨ New Resume", "📊 Match Insights"]
    if did_interview and analytics.get("interview_questions"):
        tab_labels.append("🎯 Interview Prep")
    if did_cover and analytics.get("cover_letter"):
        tab_labels.append("📝 Cover Letter")

    tabs = st.tabs(tab_labels)
    tab_idx = 0

    # ── Tab 1: New Resume ───────────────────────
    with tabs[tab_idx]:
        tab_idx += 1
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(tailored)
        st.markdown("</div>", unsafe_allow_html=True)

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                "📋 Download as Markdown",
                data=tailored,
                file_name="tailored_resume.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl_col2:
            try:
                pdf_bytes = make_resume_pdf(tailored)
                st.download_button(
                    "📄 Download as PDF",
                    data=pdf_bytes,
                    file_name="tailored_resume.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.caption(f"PDF unavailable: {e}")

    # ── Tab 2: Match Insights ───────────────────
    with tabs[tab_idx]:
        tab_idx += 1
        if not analytics:
            st.info("Analytics could not be parsed — but your tailored resume is ready above.")
        else:
            score = analytics.get("match_score", 0)
            color, bg = score_color(score)

            score_col, detail_col = st.columns([1, 2], gap="large")

            with score_col:
                fig = go.Figure(go.Pie(
                    values=[score, 100 - score],
                    hole=0.72,
                    marker_colors=[color, "#e5e7eb"],
                    textinfo="none",
                    showlegend=False,
                    hoverinfo="skip",
                ))
                fig.add_annotation(
                    text=f"<b>{score}</b><br><span style='font-size:14px'>/ 100</span>",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=28, color=color),
                    align="center",
                )
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=230,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(
                    f'<div style="background:{bg};border-radius:12px;padding:10px;text-align:center;">'
                    f'<p style="margin:0;color:{color};font-weight:600;">{analytics.get("summary","")}</p>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with detail_col:
                st.markdown("#### ✅ Strengths")
                strengths = analytics.get("strengths", [])
                badges = "".join(f'<span class="badge-green">{s}</span>' for s in strengths)
                st.markdown(badges, unsafe_allow_html=True)

                st.markdown("#### ⚠️ Skills to Build")
                missing_skills = analytics.get("missing_skills", [])
                badges2 = "".join(f'<span class="badge-amber">{s}</span>' for s in missing_skills)
                st.markdown(badges2, unsafe_allow_html=True)

                learning_path = analytics.get("learning_path", [])
                if learning_path:
                    st.markdown("#### 📚 Learning Path")
                    for item in learning_path:
                        if isinstance(item, dict):
                            skill = item.get("skill", "")
                            resources = item.get("resources", [])
                            st.markdown(f"**{skill}**")
                            for r in resources:
                                url_match = re.search(r"https?://\S+", r)
                                if url_match:
                                    link = url_match.group()
                                    label = r.replace(link, "").strip().rstrip("-–:")
                                    st.markdown(f"- [{label or link}]({link})")
                                else:
                                    st.markdown(f"- {r}")

    # ── Tab 3: Interview Prep ───────────────────
    if "🎯 Interview Prep" in tab_labels:
        with tabs[tab_idx]:
            tab_idx += 1
            questions = analytics.get("interview_questions", [])
            if not questions:
                st.info("Interview questions were not generated. Enable the toggle and re-analyze.")
            else:
                for i, q in enumerate(questions, 1):
                    if isinstance(q, dict):
                        question = q.get("question", "")
                        answer = q.get("answer", "")
                    else:
                        question = str(q)
                        answer = ""

                    with st.expander(f"**Q{i}: {question}**"):
                        if answer:
                            st.markdown(f"💬 **Model Answer:** {answer}")
                        else:
                            st.caption("Think through your answer, then reveal below.")

                try:
                    q_pdf = make_questions_pdf(questions)
                    st.download_button(
                        "📄 Download Interview Questions PDF",
                        data=q_pdf,
                        file_name="interview_prep.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.caption(f"PDF unavailable: {e}")

    # ── Tab 4: Cover Letter ─────────────────────
    if "📝 Cover Letter" in tab_labels:
        with tabs[tab_idx]:
            tab_idx += 1
            cover = analytics.get("cover_letter", "")
            if not cover:
                st.info("Cover letter was not generated. Enable the toggle and re-analyze.")
            else:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown(cover)
                st.markdown("</div>", unsafe_allow_html=True)

                cl1, cl2 = st.columns(2)
                with cl1:
                    st.download_button(
                        "📋 Download as Markdown",
                        data=cover,
                        file_name="cover_letter.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with cl2:
                    try:
                        cl_pdf = make_cover_pdf(cover)
                        st.download_button(
                            "📄 Download as PDF",
                            data=cl_pdf,
                            file_name="cover_letter.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.caption(f"PDF unavailable: {e}")
