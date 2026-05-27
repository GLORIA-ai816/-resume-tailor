
# CareerLens – Resume Tailor & Job Match Coach
# Requirements: streamlit openai PyPDF2 fpdf plotly
# CareerLens – 智能简历优化与职位匹配分析
# 依赖: streamlit openai PyPDF2 fpdf plotly
# pip install streamlit openai PyPDF2 fpdf plotly
import streamlit as st
-98
+128
from fpdf import FPDF
import plotly.graph_objects as go
API_MODEL = "glm-4-flash"
API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
API_KEY_NAME = "ZHIPUAI_API_KEY"
# ─────────────────────────────────────────────
# Page config
API_MODEL = "deepseek-chat"
API_BASE_URL = "https://api.deepseek.com"
API_KEY_NAME = "DEEPSEEK_API_KEY"
# ─────────────────────────────────────────────
# 页面配置
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CareerLens",
    page_icon="🔭",
    page_title="CareerLens - 智能简历优化与职位匹配分析",
    page_icon="[CL]",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ─────────────────────────────────────────────
# Custom CSS
# 自定义 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  /* Gradient background */
  /* 柔和奶油白背景 */
  .stApp {
    background: linear-gradient(135deg, #fdf6ec 0%, #eef4fb 50%, #e8f5f2 100%);
  }
  /* Glass cards */
  .glass-card {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.55);
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
    background: linear-gradient(160deg, #F9F9F9 0%, #F2F2F2 100%);
    color: #333333;
  }
  /* 卡片样式 */
  .cl-card {
    background: rgba(255, 255, 255, 0.88);
    border-radius: 12px;
    border: 1px solid #E0E0E0;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04);
    padding: 1.6rem 2rem;
    margin-bottom: 1.2rem;
    transition: box-shadow 0.25s ease;
  }
  .glass-card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.12); }
  /* Score ring label */
  .score-label {
    font-size: 2.6rem;
  }
  /* 欢迎横幅 */
  .welcome-banner {
    background: linear-gradient(90deg, #2C5F8A, #3A7EC4);
    color: white;
    border-radius: 10px;
    padding: 14px 22px;
    font-size: 0.97rem;
    font-weight: 500;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  /* 处理中提示 */
  .processing-hint {
    background: #F0F7FF;
    border-left: 4px solid #2C5F8A;
    border-radius: 6px;
    padding: 12px 16px;
    font-style: italic;
    color: #1A3D5C;
    margin: 1rem 0;
    font-size: 0.93rem;
  }
  /* 隐私说明 */
  .privacy-note {
    font-size: 0.76rem;
    color: #888888;
    margin-top: 0.5rem;
  }
  /* 软性警告 */
  .soft-warn {
    background: #FFFBF0;
    border-left: 3px solid #D4A017;
    border-radius: 5px;
    padding: 8px 14px;
    font-size: 0.87rem;
    color: #7A5C00;
    margin-top: 6px;
  }
  /* 匹配关键词标签 */
  .kw-tag {
    display: inline-block;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 3px 3px;
    color: #333333;
  }
  /* 优势标签 */
  .badge-ok {
    display: inline-block;
    background: #EAF5EA;
    color: #2D6A2D;
    border-radius: 5px;
    padding: 4px 14px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 3px 4px;
    border: 1px solid #C3E6C3;
  }
  /* 缺失标签 */
  .badge-gap {
    display: inline-block;
    background: #FFF5E6;
    color: #7A4500;
    border-radius: 5px;
    padding: 4px 14px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 3px 4px;
    border: 1px solid #F5CC99;
  }
  /* 对比模式标题 */
  .compare-header {
    font-size: 0.88rem;
    font-weight: 700;
    text-align: center;
  }
  /* Badge styles */
  .badge-green {
    display:inline-block;
    background:#d1fae5; color:#065f46;
    border-radius:999px; padding:3px 14px;
    font-size:0.82rem; font-weight:600;
    margin: 3px 4px;
  }
  .badge-amber {
    display:inline-block;
    background:#fef3c7; color:#92400e;
    border-radius:999px; padding:3px 14px;
    font-size:0.82rem; font-weight:600;
    margin: 3px 4px;
  }
  /* Onboarding banner */
  .onboarding-banner {
    background: linear-gradient(90deg,#6366f1,#06b6d4);
    color:white;
    border-radius:14px;
    padding:14px 22px;
    font-size:1rem;
    font-weight:500;
    margin-bottom:1.2rem;
    display:flex; align-items:center; gap:12px;
  }
  /* Thinking indicator */
  .thinking {
    background: linear-gradient(90deg,#f0fdf4,#ecfeff);
    border-left: 4px solid #34d399;
    border-radius: 8px;
    padding: 14px 18px;
    font-style: italic;
    color: #065f46;
    margin: 1rem 0;
  }
  /* Privacy note */
  .privacy-note {
    font-size:0.78rem; color:#6b7280;
    display:flex; align-items:center; gap:6px;
    margin-top: 0.5rem;
  }
  /* Soft inline warning */
  .soft-warn {
    background:#fffbeb;
    border-left: 3px solid #fbbf24;
    border-radius: 6px;
    padding: 8px 14px;
    font-size:0.88rem;
    color:#92400e;
    margin-top: 6px;
  }
  /* Sidebar styling */
  .css-1d391kg { padding-top: 1rem; }
  /* Tab label */
    color: #555555;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 6px 0;
    border-bottom: 2px solid #E0E0E0;
    margin-bottom: 0.8rem;
  }
  /* Tab 字体 */
  button[data-baseweb="tab"] {
    font-size: 0.95rem !important;
    font-size: 0.93rem !important;
    font-weight: 600 !important;
    color: #444444 !important;
  }
  /* 侧边栏背景 */
  section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E8E8E8;
  }
</style>
""", unsafe_allow_html=True)
# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def get_openai_client():
# 工具函数
# ─────────────────────────────────────────────
def get_client():
    try:
        api_key = st.secrets["ZHIPUAI_API_KEY"]
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        return None, "missing_key"
    return openai.OpenAI(api_key=api_key, base_url=API_BASE_URL), None
-36
+41
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"
        return f"[PDF 解析失败: {e}]"
def resume_health_check(resume_text: str) -> list[str]:
    hints = []
    low = resume_text.lower()
    if not re.search(r"[\w.+-]+@[\w-]+\.\w+", resume_text):
        hints.append("Looks like an email address is missing — recruiters need a way to reach you.")
    if not re.search(r"\d{3}[\s\-.]?\d{3}[\s\-.]?\d{4}", resume_text):
        hints.append("Consider adding a phone number for a complete contact section.")
    if "linkedin" not in low and "github" not in low:
        hints.append("A LinkedIn or GitHub URL can strengthen first impressions.")
        hints.append("未检测到邮箱地址，建议补充联系方式。")
    if not re.search(r"1[3-9]\d{9}|(\+\d{1,3}[\s-])?\(?\d{3}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{4}", resume_text):
        hints.append("未检测到手机号，招聘方需要能联系到您的方式。")
    if "linkedin" not in low and "github" not in low and "gitee" not in low:
        hints.append("建议添加 LinkedIn、GitHub 或 Gitee 链接，增强个人品牌。")
    if len(resume_text.split()) < 150:
        hints.append("Your resume feels brief — a bit more detail about your experience can help.")
    if "objective" in low or "references available" in low:
        hints.append("Objective statements & 'references available' are outdated — consider removing them.")
        hints.append("简历内容偏少，建议补充更多工作经历和项目成果。")
    if "求职目标" in resume_text or "references available" in low:
        hints.append("「求职目标」和「可提供推荐信」等语句已过时，建议删除。")
    return hints
def build_system_prompt(style: str, gen_cover: bool, gen_interview: bool) -> str:
    style_notes = {
        "Modern & Warm": "Use a warm, approachable tone with active verbs and relatable language.",
        "Professional": "Use a formal, concise, executive tone — no fluff.",
        "Academic": "Use precise language, emphasise projects, research, and methodologies if present.",
        "现代 & 亲切": "请使用积极、亲切的语气，多用动态动词和量化成果，让简历充满活力。",
        "专业 & 严谨": "请使用正式、简洁的商务语言，突出核心成就，避免冗余表述。",
        "学术 & 规范": "请使用规范的学术语言，重点突出项目成果、科研经历和专业技能。",
    }
    extras = []
    if gen_cover:
        extras.append(
            '"cover_letter": a tailored cover letter (3-4 paragraphs, <300 words) '
            'that merges the resume\'s voice with the job description\'s tone.'
            '"cover_letter": 一封有针对性的求职信（3-4段，不超过400字），'
            '融合简历亮点与职位描述的语气，语言自然真诚，不浮夸。'
        )
    if gen_interview:
        extras.append(
            '"interview_questions": a list of exactly 5 likely interview questions for this role, '
            'each as an object with "question" (string) and "answer" (string, concise model answer, 2-4 sentences).'
            '"interview_questions": 针对该职位最可能考察的5个面试问题列表，'
            '每项为包含 "question"（问题）和 "answer"（简明参考答案，2-4句）的对象。'
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
    return f"""你是一位资深职业顾问和简历专家，精通中国求职市场。{style_notes.get(style, '')}
你的任务：
1. 仔细阅读候选人的简历和目标职位描述（JD）。
2. 生成一份优化后的简历，要求：
   - 突出与JD高度匹配的关键词和量化成就。
   - 绝不捏造经历或技能，只重新组织和优化已有内容。
   - 以结构清晰的 Markdown 格式输出。
3. 同时生成一份 JSON 分析报告。
重要——你的回复必须严格遵循如下格式，不得在格式前后添加任何其他内容：
TAILORED_RESUME_START
<the tailored resume in Markdown here>
<优化后的简历 Markdown 内容>
TAILORED_RESUME_END
ANALYTICS_START
{{
  "match_score": <integer 0-100>,
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "missing_skills": ["<skill 1>", "<skill 2>", "<skill 3>"],
  "match_score": <整体匹配度，整数 0-100>,
  "skill_match": <技能匹配度，整数 0-100>,
  "experience_match": <经验匹配度，整数 0-100>,
  "education_match": <教育背景匹配度，整数 0-100>,
  "strengths": ["<优势1>", "<优势2>", "<优势3>"],
  "missing_skills": ["<缺失技能1>", "<缺失技能2>", "<缺失技能3>"],
  "matched_keywords": ["<已匹配关键词1>", "<关键词2>", "<关键词3>", "<关键词4>", "<关键词5>"],
  "missing_keywords": ["<缺失关键词1>", "<关键词2>", "<关键词3>"],
  "learning_path": [
    {{"skill": "<skill>", "resources": ["<free resource or course name + URL>", "<resource 2>"]}},
    {{"skill": "<skill>", "resources": ["<free resource or course name + URL>", "<resource 2>"]}}
    {{"skill": "<技能>", "resources": ["<免费学习资源名称+链接>", "<资源2>"]}},
    {{"skill": "<技能>", "resources": ["<免费学习资源名称+链接>", "<资源2>"]}}
  ],
  "summary": "<2-sentence encouraging explanation of fit>"{"," if extras else ""}
  "summary": "<2句话，鼓励性地总结候选人与职位的匹配度>"{"," if extras else ""}
  {extra_fields.strip()}
}}
ANALYTICS_END"""
def call_openai(client, model: str, resume: str, jd: str, system_prompt: str) -> str:
def call_api(client, resume: str, jd: str, system_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=API_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"RESUME:\n{resume}\n\n---\n\nJOB DESCRIPTION:\n{jd}"},
                {"role": "user", "content": f"【我的简历】\n{resume}\n\n---\n\n【目标职位描述】\n{jd}"},
            ],
            max_tokens=4096,
            temperature=0.4,
-0
+2
        return "RATE_LIMIT"
    except openai.AuthenticationError:
        return "AUTH_ERROR"
    except openai.APIConnectionError:
        return "CONN_ERROR"
    except Exception as e:
        return f"ERROR:{e}"
-2
+2
    return tailored, analytics
def make_resume_pdf(tailored_resume: str) -> bytes:
def make_resume_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Helvetica", ...
[truncated]
[truncated]
[truncated]
-1
+1
[truncated]
[truncated]
-1
+1
[truncated]
[truncated]
-1
+1
[truncated]
[truncated]
-1
+1
[truncated]
[truncated]
-1
+1
[truncated]
[truncated]
-1
+1
[truncated]
[truncated]
