# CareerLens – 智能简历优化与职位匹配分析
# 依赖: streamlit openai PyPDF2 fpdf plotly
# pip install streamlit openai PyPDF2 fpdf plotly

import streamlit as st
import openai
import json
import re
from fpdf import FPDF
import plotly.graph_objects as go

API_MODEL = "deepseek-chat"
API_BASE_URL = "https://api.deepseek.com"
API_KEY_NAME = "DEEPSEEK_API_KEY"

# ─────────────────────────────────────────────
# 页面配置
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CareerLens - 智能简历优化与职位匹配分析",
    page_icon="[CL]",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 自定义 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  .stApp {
    background: linear-gradient(160deg, #F9F9F9 0%, #F2F2F2 100%);
    color: #333333;
  }
  .cl-card {
    background: rgba(255, 255, 255, 0.88);
    border-radius: 12px;
    border: 1px solid #E0E0E0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
    padding: 1.6rem 2rem;
    margin-bottom: 1.2rem;
  }
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
  .privacy-note {
    font-size: 0.76rem;
    color: #888888;
    margin-top: 0.5rem;
  }
  .soft-warn {
    background: #FFFBF0;
    border-left: 3px solid #D4A017;
    border-radius: 5px;
    padding: 8px 14px;
    font-size: 0.87rem;
    color: #7A5C00;
    margin-top: 6px;
  }
  .kw-tag {
    display: inline-block;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 3px 3px;
    color: #333333;
  }
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
  .compare-header {
    font-size: 0.88rem;
    font-weight: 700;
    color: #555555;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 6px 0;
    border-bottom: 2px solid #E0E0E0;
    margin-bottom: 0.8rem;
  }
  button[data-baseweb="tab"] {
    font-size: 0.93rem !important;
    font-weight: 600 !important;
    color: #444444 !important;
  }
  section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E8E8E8;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def get_client():
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        return None, "missing_key"
    return openai.OpenAI(api_key=api_key, base_url=API_BASE_URL), None


def extract_pdf_text(uploaded_file) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"[PDF 解析失败: {e}]"


def resume_health_check(resume_text: str) -> list:
    hints = []
    low = resume_text.lower()
    if not re.search(r"[\w.+-]+@[\w-]+\.\w+", resume_text):
        hints.append("未检测到邮箱地址，建议补充联系方式。")
    if not re.search(r"1[3-9]\d{9}|(\+\d{1,3}[\s-])?\(?\d{3}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{4}", resume_text):
        hints.append("未检测到手机号，招聘方需要能联系到您的方式。")
    if "linkedin" not in low and "github" not in low and "gitee" not in low:
        hints.append("建议添加 LinkedIn、GitHub 或 Gitee 链接，增强个人品牌。")
    if len(resume_text.split()) < 150:
        hints.append("简历内容偏少，建议补充更多工作经历和项目成果。")
    if "求职目标" in resume_text or "references available" in low:
        hints.append("「求职目标」和「可提供推荐信」等语句已过时，建议删除。")
    return hints


def build_system_prompt(style: str, gen_cover: bool, gen_interview: bool) -> str:
    style_notes = {
        "现代 & 亲切": "请使用积极、亲切的语气，多用动态动词和量化成果，让简历充满活力。",
        "专业 & 严谨": "请使用正式、简洁的商务语言，突出核心成就，避免冗余表述。",
        "学术 & 规范": "请使用规范的学术语言，重点突出项目成果、科研经历和专业技能。",
    }
    extras = []
    if gen_cover:
        extras.append(
            '"cover_letter": 一封有针对性的求职信（3-4段，不超过400字），'
            '融合简历亮点与职位描述的语气，语言自然真诚，不浮夸。'
        )
    if gen_interview:
        extras.append(
            '"interview_questions": 针对该职位最可能考察的5个面试问题列表，'
            '每项为包含 "question"（问题）和 "answer"（简明参考答案，2-4句）的对象。'
        )

    extra_fields = ("\n" + "\n".join(f"      - {e}" for e in extras)) if extras else ""
    comma = "," if extras else ""

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
<优化后的简历 Markdown 内容>
TAILORED_RESUME_END

ANALYTICS_START
{{
  "match_score": <整体匹配度，整数 0-100>,
  "skill_match": <技能匹配度，整数 0-100>,
  "experience_match": <经验匹配度，整数 0-100>,
  "education_match": <教育背景匹配度，整数 0-100>,
  "strengths": ["<优势1>", "<优势2>", "<优势3>"],
  "missing_skills": ["<缺失技能1>", "<缺失技能2>", "<缺失技能3>"],
  "matched_keywords": ["<已匹配关键词1>", "<关键词2>", "<关键词3>", "<关键词4>", "<关键词5>"],
  "missing_keywords": ["<缺失关键词1>", "<关键词2>", "<关键词3>"],
  "learning_path": [
    {{"skill": "<技能>", "resources": ["<免费学习资源名称+链接>", "<资源2>"]}},
    {{"skill": "<技能>", "resources": ["<免费学习资源名称+链接>", "<资源2>"]}}
  ],
  "summary": "<2句话，鼓励性地总结候选人与职位的匹配度>"{comma}
  {extra_fields.strip()}
}}
ANALYTICS_END"""


def call_api(client, resume: str, jd: str, system_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=API_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"【我的简历】\n{resume}\n\n---\n\n【目标职位描述】\n{jd}"},
            ],
            max_tokens=4096,
            temperature=0.4,
        )
        return response.choices[0].message.content
    except openai.RateLimitError:
        return "RATE_LIMIT"
    except openai.AuthenticationError:
        return "AUTH_ERROR"
    except openai.APIConnectionError:
        return "CONN_ERROR"
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


def make_resume_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Helvetica", size=11)
    for line in text.split("\n"):
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
            pdf.multi_cell(0, 6, f"  * {clean}")
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
    pdf.cell(0, 12, "Interview Preparation - CareerLens", ln=True)
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


def make_cover_pdf(cover: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(22, 22, 22)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Cover Letter - CareerLens", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.ln(3)
    for para in cover.split("\n\n"):
        pdf.multi_cell(0, 6, para.strip())
        pdf.ln(4)
    return bytes(pdf.output())


def score_color(score: int):
    if score >= 75:
        return "#2D7A2D", "#EAF5EA"
    elif score >= 50:
        return "#A05C00", "#FFF5E6"
    else:
        return "#8B3A00", "#FFF0E6"


def render_donut(score: int, title: str = "") -> go.Figure:
    color, _ = score_color(score)
    fig = go.Figure(go.Pie(
        values=[score, 100 - score],
        hole=0.74,
        marker_colors=[color, "#EBEBEB"],
        textinfo="none",
        showlegend=False,
        hoverinfo="skip",
    ))
    label = f"<b>{score}</b><br><span style='font-size:11px'>{title}</span>" if title else f"<b>{score}</b><br><span style='font-size:12px'>/ 100</span>"
    fig.add_annotation(
        text=label, x=0.5, y=0.5,
        showarrow=False, font=dict(size=22, color=color), align="center",
    )
    fig.update_layout(
        margin=dict(t=5, b=5, l=5, r=5),
        height=170,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def render_skill_bar(matched: list, missing: list) -> go.Figure:
    labels = [f"[匹配] {k}" for k in matched] + [f"[缺失] {k}" for k in missing]
    values = [1] * (len(matched) + len(missing))
    colors = ["#4A9E4A"] * len(matched) + ["#D47A00"] * len(missing)
    texts = ["已具备"] * len(matched) + ["待提升"] * len(missing)

    fig = go.Figure(go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker_color=colors,
        text=texts,
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", size=11),
        hoverinfo="skip",
    ))
    fig.update_layout(
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#333333")),
        margin=dict(t=10, b=10, l=10, r=10),
        height=max(200, 36 * len(labels)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.35,
    )
    return fig


def render_keyword_cloud(matched: list, missing: list) -> str:
    sizes = [1.05, 0.92, 1.1, 0.88, 1.0, 0.95, 1.08, 0.9]
    html = '<div style="line-height:2.4; padding: 6px 0;">'
    for i, kw in enumerate(matched):
        sz = sizes[i % len(sizes)]
        html += (
            f'<span class="kw-tag" style="background:#EAF5EA;color:#2D6A2D;'
            f'border:1px solid #C3E6C3;font-size:{sz}rem;">{kw}</span>'
        )
    for i, kw in enumerate(missing):
        sz = sizes[(i + 3) % len(sizes)]
        html += (
            f'<span class="kw-tag" style="background:#FFF5E6;color:#7A4500;'
            f'border:1px solid #F5CC99;font-size:{sz}rem;">{kw}</span>'
        )
    html += "</div>"
    return html


# ─────────────────────────────────────────────
# 侧边栏
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## CareerLens")
    st.caption("智能简历优化 · 职位匹配分析")
    st.divider()

    resume_style = st.selectbox(
        "简历风格",
        ["现代 & 亲切", "专业 & 严谨", "学术 & 规范"],
    )
    gen_cover = st.toggle("生成求职信", value=True)
    gen_interview = st.toggle("生成面试题", value=True)

    st.selectbox(
        "AI 模型",
        [API_MODEL],
        help="当前使用 DeepSeek Chat 模型，性能强劲，响应快速。",
    )

    st.divider()

    if st.button("重置清空", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.divider()
    st.markdown("**关于本项目**")
    st.caption(
        "CareerLens 是一款基于 AI 的智能求职工具，"
        "帮助您分析简历与职位的匹配度、优化简历内容、生成面试准备材料。\n\n"
        "技术栈：Streamlit · DeepSeek API · Plotly · fpdf"
    )
    st.markdown(
        '<div class="privacy-note">[ 安全 ] 您的数据仅用于本次分析，不会被存储或传输至第三方。</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# 主界面
# ─────────────────────────────────────────────

if "onboarding_dismissed" not in st.session_state:
    st.markdown(
        '<div class="welcome-banner">'
        '<strong>欢迎使用 CareerLens</strong> — '
        '粘贴您的简历和目标职位，AI 将为您生成专属优化方案。'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("知道了，关闭提示", key="dismiss_onboarding"):
        st.session_state["onboarding_dismissed"] = True
        st.rerun()

client, key_error = get_client()
if key_error == "missing_key":
    st.error(
        "**未找到 DeepSeek API Key**\n\n"
        "请按以下步骤配置：\n"
        "1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) 获取 API Key\n"
        "2. 在项目根目录创建 `.streamlit/secrets.toml` 文件\n"
        "3. 添加一行：`DEEPSEEK_API_KEY = \"sk-your-key-here\"`\n"
        "4. 重启应用即可生效"
    )
    st.stop()

# 输入区域
st.markdown("## 简历与职位信息")

col_resume, col_jd = st.columns(2, gap="large")

with col_resume:
    st.markdown("#### 我的简历")
    uploaded = st.file_uploader(
        "上传简历（支持 .txt 或 .pdf）",
        type=["txt", "pdf"],
    )
    resume_text = ""
    if uploaded:
        if uploaded.type == "application/pdf":
            resume_text = extract_pdf_text(uploaded)
            st.success(f"PDF 解析完成，共提取 {len(resume_text)} 个字符。")
        else:
            resume_text = uploaded.read().decode("utf-8", errors="ignore")

    resume_input = st.text_area(
        "或直接粘贴简历内容",
        value=resume_text,
        height=320,
        placeholder="将您的简历全文粘贴于此…",
    )

    if resume_input.strip():
        hints = resume_health_check(resume_input)
        if hints:
            with st.expander("简历健康检查建议", expanded=True):
                for h in hints:
                    st.markdown(f'<div class="soft-warn">! {h}</div>', unsafe_allow_html=True)

with col_jd:
    st.markdown("#### 目标职位描述（JD）")
    jd_input = st.text_area(
        "粘贴职位描述",
        height=380,
        placeholder="将目标职位的招聘说明全文粘贴于此…",
        label_visibility="collapsed",
    )

st.markdown("<br>", unsafe_allow_html=True)

run_col, _ = st.columns([1, 3])
with run_col:
    analyze_clicked = st.button(
        "开始分析与优化",
        type="primary",
        use_container_width=True,
    )

if analyze_clicked:
    missing_inputs = []
    if not resume_input.strip():
        missing_inputs.append("简历")
    if not jd_input.strip():
        missing_inputs.append("职位描述")
    if missing_inputs:
        st.markdown(
            f'<div class="soft-warn">请先填写{" 和 ".join(missing_inputs)}，再开始分析。</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="processing-hint">AI 正在分析您的简历与职位匹配情况，通常需要 20-40 秒，请稍候…</div>',
            unsafe_allow_html=True,
        )
        with st.spinner(""):
            system_prompt = build_system_prompt(resume_style, gen_cover, gen_interview)
            raw = call_api(client, resume_input, jd_input, system_prompt)

        if raw == "RATE_LIMIT":
            st.warning("请求过于频繁，请等待约 60 秒后重试。DeepSeek API 有请求频率限制。")
        elif raw == "AUTH_ERROR":
            st.error("API Key 验证失败。请检查 `DEEPSEEK_API_KEY` 是否正确填写，以及 Key 是否已过期。")
        elif raw == "CONN_ERROR":
            st.error("无法连接到 DeepSeek API，请检查网络连接后重试。")
        elif raw.startswith("ERROR:"):
            st.error(f"发生未知错误：{raw[6:]}")
        else:
            tailored, analytics = parse_response(raw)
            st.session_state["tailored"] = tailored
            st.session_state["original"] = resume_input
            st.session_state["analytics"] = analytics
            st.session_state["gen_cover"] = gen_cover
            st.session_state["gen_interview"] = gen_interview
            st.rerun()

# ─────────────────────────────────────────────
# 结果展示
# ─────────────────────────────────────────────
if "tailored" in st.session_state:
    tailored = st.session_state["tailored"]
    original = st.session_state.get("original", "")
    analytics = st.session_state["analytics"]
    did_cover = st.session_state.get("gen_cover", False)
    did_interview = st.session_state.get("gen_interview", False)

    st.markdown("---")
    st.markdown("## 分析结果")

    tab_labels = ["优化简历", "匹配洞察"]
    if did_interview and analytics.get("interview_questions"):
        tab_labels.append("面试准备")
    if did_cover and analytics.get("cover_letter"):
        tab_labels.append("求职信")

    tabs = st.tabs(tab_labels)
    tab_idx = 0

    # Tab 1：优化简历
    with tabs[tab_idx]:
        tab_idx += 1
        compare_mode = st.toggle("对比模式（同时查看原版与优化版）", value=False)

        if compare_mode and original:
            col_orig, col_new = st.columns(2, gap="medium")
            with col_orig:
                st.markdown('<div class="compare-header">原版简历</div>', unsafe_allow_html=True)
                st.text_area("原版", value=original, height=600, label_visibility="collapsed")
            with col_new:
                st.markdown('<div class="compare-header">AI 优化版</div>', unsafe_allow_html=True)
                st.markdown('<div class="cl-card">', unsafe_allow_html=True)
                st.markdown(tailored)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="cl-card">', unsafe_allow_html=True)
            st.markdown(tailored)
            st.markdown("</div>", unsafe_allow_html=True)

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "下载 Markdown 版本",
                data=tailored,
                file_name="优化简历_CareerLens.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl2:
            try:
                pdf_bytes = make_resume_pdf(tailored)
                st.download_button(
                    "下载 PDF 版本",
                    data=pdf_bytes,
                    file_name="优化简历_CareerLens.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.caption(f"PDF 生成失败：{e}")

    # Tab 2：匹配洞察
    with tabs[tab_idx]:
        tab_idx += 1
        if not analytics:
            st.info("分析数据解析失败，但您的优化简历已生成，请切换到「优化简历」标签查看。")
        else:
            overall = analytics.get("match_score", 0)
            skill_s = analytics.get("skill_match", 0)
            exp_s = analytics.get("experience_match", 0)
            edu_s = analytics.get("education_match", 0)
            summary = analytics.get("summary", "")
            strengths = analytics.get("strengths", [])
            missing_skills = analytics.get("missing_skills", [])
            matched_kw = analytics.get("matched_keywords", [])
            missing_kw = analytics.get("missing_keywords", [])
            learning_path = analytics.get("learning_path", [])

            st.markdown("#### 综合匹配度")
            d1, d2, d3, d4 = st.columns(4)
            with d1:
                st.plotly_chart(render_donut(overall, "综合"), use_container_width=True, key="d_overall")
            with d2:
                st.plotly_chart(render_donut(skill_s, "技能"), use_container_width=True, key="d_skill")
            with d3:
                st.plotly_chart(render_donut(exp_s, "经验"), use_container_width=True, key="d_exp")
            with d4:
                st.plotly_chart(render_donut(edu_s, "教育"), use_container_width=True, key="d_edu")

            if summary:
                color, bg = score_color(overall)
                st.markdown(
                    f'<div class="cl-card" style="background:{bg};border-color:{color}22;">'
                    f'<p style="margin:0;color:{color};font-weight:600;">{summary}</p></div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            if matched_kw or missing_kw:
                st.markdown("#### 职位关键词分析")
                st.markdown(render_keyword_cloud(matched_kw, missing_kw), unsafe_allow_html=True)
                st.caption("绿色 = 您已具备的关键词　　橙色 = 职位要求但简历中未体现")
                st.markdown("")

            if matched_kw or missing_kw:
                st.markdown("#### 技能匹配详情")
                st.plotly_chart(render_skill_bar(matched_kw, missing_kw), use_container_width=True, key="bar_skills")

            st.markdown("---")

            adv_col, gap_col = st.columns(2)
            with adv_col:
                st.markdown("#### 您的竞争优势")
                badges = "".join(f'<span class="badge-ok">{s}</span>' for s in strengths)
                st.markdown(badges or "<i>暂无数据</i>", unsafe_allow_html=True)
            with gap_col:
                st.markdown("#### 需要补充的能力")
                badges2 = "".join(f'<span class="badge-gap">{s}</span>' for s in missing_skills)
                st.markdown(badges2 or "<i>暂无数据</i>", unsafe_allow_html=True)

            if learning_path:
                st.markdown("---")
                st.markdown("#### 推荐学习路径")
                for item in learning_path:
                    if isinstance(item, dict):
                        skill = item.get("skill", "")
                        resources = item.get("resources", [])
                        st.markdown(f"**{skill}**")
                        for r in resources:
                            url_match = re.search(r"https?://\S+", r)
                            if url_match:
                                link = url_match.group()
                                label = r.replace(link, "").strip().rstrip("-–:：")
                                st.markdown(f"- [{label or link}]({link})")
                            else:
                                st.markdown(f"- {r}")

    # Tab 3：面试准备
    if "面试准备" in tab_labels:
        with tabs[tab_idx]:
            tab_idx += 1
            questions = analytics.get("interview_questions", [])
            if not questions:
                st.info("面试题未生成，请在侧边栏开启「生成面试题」后重新分析。")
            else:
                st.markdown("点击每道题展开参考答案，建议先自己思考再查看。")
                for i, q in enumerate(questions, 1):
                    question = q.get("question", "") if isinstance(q, dict) else str(q)
                    answer = q.get("answer", "") if isinstance(q, dict) else ""
                    with st.expander(f"Q{i}：{question}"):
                        if answer:
                            st.markdown(f"**参考答案：** {answer}")
                        else:
                            st.caption("请自行思考作答。")

                try:
                    q_pdf = make_questions_pdf(questions)
                    st.download_button(
                        "下载面试题 PDF",
                        data=q_pdf,
                        file_name="面试准备_CareerLens.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.caption(f"PDF 生成失败：{e}")

    # Tab 4：求职信
    if "求职信" in tab_labels:
        with tabs[tab_idx]:
            tab_idx += 1
            cover = analytics.get("cover_letter", "")
            if not cover:
                st.info("求职信未生成，请在侧边栏开启「生成求职信」后重新分析。")
            else:
                st.markdown('<div class="cl-card">', unsafe_allow_html=True)
                st.markdown(cover)
                st.markdown("</div>", unsafe_allow_html=True)

                cl1, cl2 = st.columns(2)
                with cl1:
                    st.download_button(
                        "下载 Markdown 版本",
                        data=cover,
                        file_name="求职信_CareerLens.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with cl2:
                    try:
                        cl_pdf = make_cover_pdf(cover)
                        st.download_button(
                            "下载 PDF 版本",
                            data=cl_pdf,
                            file_name="求职信_CareerLens.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.caption(f"PDF 生成失败：{e}")
