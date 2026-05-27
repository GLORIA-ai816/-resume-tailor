# pip install streamlit openai PyPDF2 fpdf plotly
# difflib、json、re、io、html、pathlib、tempfile、urllib 等为 Python 标准库，无需单独安装。

import difflib
import html
import io
import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError
from PyPDF2 import PdfReader


# =========================
# 全局配置
# =========================

API_MODEL = "deepseek-chat"
API_BASE_URL = "https://api.deepseek.com"
API_KEY_NAME = "DEEPSEEK_API_KEY"

APP_NAME = "CareerLens – 智能简历优化与职位匹配分析"
FONT_STACK = '"Inter", "Helvetica Neue", "Arial", "PingFang SC", "Microsoft YaHei", sans-serif'


st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================
# 全局样式
# =========================

st.markdown(
    """
<style>
    :root {
        --bg: #FBFBFB;
        --card: #FFFFFF;
        --line: #F0F0F0;
        --line-strong: #E6E6E6;
        --text: #1A1A1A;
        --muted: #6B6B6B;
        --primary: #2C2C2C;
        --primary-hover: #3D3D3D;
        --success: #1F7A5C;
        --amber: #B78B3D;
        --danger-soft: #C26A5C;
        --tag: #F3F3F3;
        --notice: #F7F7F7;
        --amber-bg: #FFFBF2;
    }

    html, body, [class*="css"], .stApp {
        font-family: "Inter", "Helvetica Neue", "Arial", "PingFang SC", "Microsoft YaHei", sans-serif;
        color: var(--text);
    }

    .stApp {
        background: var(--bg);
    }

    .main .block-container {
        max-width: 1040px;
        padding: 2.4rem 2rem 4rem;
    }

    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] * {
        font-family: "Inter", "Helvetica Neue", "Arial", "PingFang SC", "Microsoft YaHei", sans-serif;
    }

    h1, h2, h3 {
        color: var(--text);
        letter-spacing: 0;
        font-weight: 600;
    }

    h1 {
        font-size: 2rem;
        line-height: 1.25;
        margin-bottom: 0.35rem;
    }

    h2 {
        font-size: 1.25rem;
        line-height: 1.35;
    }

    h3 {
        font-size: 1rem;
        line-height: 1.45;
    }

    p, li, label, .stMarkdown {
        font-size: 14px;
        line-height: 1.6;
    }

    .muted {
        color: var(--muted);
    }

    .app-title {
        font-size: 1.82rem;
        font-weight: 600;
        letter-spacing: 0;
        line-height: 1.25;
        margin: 0;
    }

    .app-subtitle {
        color: var(--muted);
        font-size: 14px;
        line-height: 1.7;
        margin: 0.35rem 0 1.4rem;
        max-width: 760px;
    }

    .sidebar-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text);
        margin: 0.2rem 0 0.35rem;
    }

    .sidebar-desc {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.65;
        margin-bottom: 1.2rem;
    }

    .welcome-card,
    .notice-card,
    .metric-card,
    .learning-card,
    .soft-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
    }

    .welcome-card {
        padding: 1rem 1.1rem;
        margin-bottom: 1.4rem;
        color: var(--muted);
        font-size: 14px;
        line-height: 1.65;
    }

    .notice-card {
        padding: 1rem 1.1rem;
        color: var(--muted);
        margin: 1rem 0;
    }

    .metric-card {
        padding: 1.25rem 1.35rem;
        min-height: 100%;
    }

    .learning-card {
        padding: 1rem 1.05rem;
        margin-bottom: 0.75rem;
    }

    .soft-card {
        padding: 1rem 1.05rem;
        margin-bottom: 0.75rem;
    }

    .small-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text);
        margin: 0 0 0.35rem;
    }

    .small-text {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.65;
        margin: 0;
    }

    .health-item {
        background: var(--amber-bg);
        border-left: 2px solid #D3AA5F;
        border-top: 1px solid #F3E7CF;
        border-right: 1px solid #F3E7CF;
        border-bottom: 1px solid #F3E7CF;
        border-radius: 6px;
        color: #5F513B;
        font-size: 13px;
        line-height: 1.6;
        padding: 0.72rem 0.82rem;
        margin: 0.55rem 0;
    }

    .health-ok {
        background: #F7FAF8;
        border-left: 2px solid var(--success);
        border-top: 1px solid #E6F0EA;
        border-right: 1px solid #E6F0EA;
        border-bottom: 1px solid #E6F0EA;
        border-radius: 6px;
        color: #38584B;
        font-size: 13px;
        line-height: 1.6;
        padding: 0.72rem 0.82rem;
        margin: 0.55rem 0;
    }

    .tag-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.5rem 0 1rem;
    }

    .tag {
        display: inline-flex;
        align-items: center;
        background: var(--tag);
        color: #4D4D4D;
        border-radius: 20px;
        padding: 0.28rem 0.68rem;
        font-size: 12px;
        line-height: 1.4;
        white-space: normal;
    }

    .tag-amber {
        background: #F7F1E8;
        color: #6A5633;
    }

    .tag-green {
        background: #EEF6F2;
        color: #245B49;
    }

    .metric-row {
        margin: 0.95rem 0 1.15rem;
    }

    .metric-label {
        display: flex;
        justify-content: space-between;
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 0.42rem;
    }

    .metric-label strong {
        color: var(--text);
        font-weight: 500;
    }

    .thin-progress {
        height: 4px;
        width: 100%;
        background: #F1F1F1;
        border-radius: 99px;
        overflow: hidden;
    }

    .thin-progress-fill {
        height: 4px;
        border-radius: 99px;
    }

    .resource-link {
        color: var(--primary);
        text-decoration: none;
        border-bottom: 1px solid #D8D8D8;
    }

    .resource-link:hover {
        color: var(--primary-hover);
        border-bottom-color: var(--primary-hover);
    }

    .cover-letter {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1.35rem 1.45rem;
        line-height: 1.75;
        white-space: pre-wrap;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
    }

    hr {
        border: none;
        border-top: 1px solid var(--line);
        margin: 1.4rem 0;
    }

    .stTextArea textarea,
    .stTextInput input,
    .stSelectbox [data-baseweb="select"],
    .stFileUploader [data-testid="stFileUploaderDropzone"] {
        background: #FFFFFF !important;
        border: 1px solid var(--line-strong) !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        color: var(--text) !important;
    }

    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: #B3B3B3 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    .stTextArea textarea::placeholder {
        color: #9A9A9A !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] {
        font-size: 0 !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"]::before {
        content: "拖放 TXT/PDF 文件到此处，或点击选择";
        display: block;
        font-size: 13px;
        color: var(--muted);
        line-height: 1.5;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] small {
        display: none !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        font-size: 0 !important;
    }

    [data-testid="stFileUploaderDropzone"] button::after {
        content: "选择文件";
        font-size: 13px;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 6px !important;
        border: 1px solid var(--line-strong) !important;
        background: #FFFFFF !important;
        color: var(--primary) !important;
        box-shadow: none !important;
        font-weight: 500 !important;
        transition: none !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #D2D2D2 !important;
        color: var(--primary-hover) !important;
        background: #FAFAFA !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--primary) !important;
        color: #FFFFFF !important;
        border-color: var(--primary) !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--primary-hover) !important;
        border-color: var(--primary-hover) !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stExpander"] {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }

    div[data-testid="stExpander"] summary {
        font-weight: 500;
        color: var(--text);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
        border-bottom: 1px solid var(--line);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        color: var(--muted);
        font-weight: 500;
        padding: 0.65rem 0.9rem;
    }

    .stTabs [aria-selected="true"] {
        color: var(--text);
        background: #FFFFFF;
    }

    [data-testid="stAlert"] {
        border-radius: 8px;
        border: 1px solid var(--line);
        box-shadow: none;
    }

    div[data-testid="stMetricValue"] {
        color: var(--text);
        font-weight: 600;
    }

    .diff-wrapper {
        font-family: "Inter", "Helvetica Neue", "Arial", "PingFang SC", "Microsoft YaHei", sans-serif;
        font-size: 12px;
        color: #1A1A1A;
        background: #FFFFFF;
    }

    .diff-wrapper table.diff {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #F0F0F0;
    }

    .diff-wrapper .diff_header {
        background: #F7F7F7;
        color: #4D4D4D;
        font-weight: 500;
    }

    .diff-wrapper td {
        padding: 0.25rem 0.35rem;
        border-top: 1px solid #F3F3F3;
        vertical-align: top;
    }

    .diff-wrapper .diff_add {
        background: #EEF6F2;
    }

    .diff-wrapper .diff_chg {
        background: #F7F1E8;
    }

    .diff-wrapper .diff_sub {
        background: #FAF0EE;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# 基础工具函数
# =========================


def init_session_state() -> None:
    """初始化页面状态。"""
    defaults = {
        "resume_text": "",
        "jd_text": "",
        "analysis_result": None,
        "welcome_visible": True,
        "confirm_reset": False,
        "uploaded_resume_signature": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def safe_html(value: object) -> str:
    """安全转义 HTML 文本。"""
    return html.escape(str(value or ""), quote=True)


def clamp_score(value: object) -> int:
    """将模型返回分数规整到 0-100。"""
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = 0
    return max(0, min(100, score))


def score_color(score: int) -> str:
    """根据分数返回克制的状态色。"""
    if score >= 78:
        return "#1F7A5C"
    if score >= 55:
        return "#B78B3D"
    return "#C26A5C"


def show_notice(message: str) -> None:
    """展示温和提示卡片。"""
    st.markdown(
        f'<div class="notice-card">{safe_html(message)}</div>',
        unsafe_allow_html=True,
    )


def get_api_key() -> str:
    """从 Streamlit Secrets 中读取 API Key。"""
    try:
        return str(st.secrets[API_KEY_NAME]).strip()
    except Exception:
        return ""


def create_openai_client(api_key: str) -> OpenAI:
    """创建 OpenAI 兼容客户端。"""
    return OpenAI(api_key=api_key, base_url=API_BASE_URL)


def reset_workspace() -> None:
    """清空当前会话内容。"""
    for key in [
        "resume_text",
        "jd_text",
        "analysis_result",
        "confirm_reset",
        "uploaded_resume_signature",
    ]:
        if key in st.session_state:
            if key == "confirm_reset":
                st.session_state[key] = False
            else:
                st.session_state[key] = "" if key != "analysis_result" else None
    st.rerun()


# =========================
# 文件读取与健康检查
# =========================


def extract_pdf_text(uploaded_file) -> str:
    """从 PDF 中提取文本。"""
    try:
        reader = PdfReader(uploaded_file)
        parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                parts.append(page_text.strip())
        return "\n\n".join(parts).strip()
    except Exception as exc:
        raise ValueError("PDF 解析失败，请确认文件未加密且包含可提取文本。") from exc


def extract_txt_text(uploaded_file) -> str:
    """从 TXT 中提取文本，兼容常见中文编码。"""
    raw = uploaded_file.getvalue()
    for encoding in ["utf-8", "utf-8-sig", "gb18030", "gbk"]:
        try:
            return raw.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore").strip()


def load_resume_file(uploaded_file) -> str:
    """根据文件类型读取简历文本。"""
    if uploaded_file is None:
        return ""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(uploaded_file)
    if suffix == ".txt":
        return extract_txt_text(uploaded_file)
    raise ValueError("仅支持上传 .txt 或 .pdf 文件。")


def estimate_word_count(text: str) -> int:
    """估算中英文混合简历的词量。"""
    english_words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", text)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    return len(english_words) + max(0, len(cjk_chars) // 2)


def resume_health_checks(text: str) -> list[str]:
    """返回简历健康检查建议。"""
    cleaned = text.strip()
    if not cleaned:
        return ["粘贴或上传简历后，这里会显示可执行的优化建议。"]

    suggestions = []
    if not re.search(r"[\w.\-+%]+@[\w.\-]+\.[A-Za-z]{2,}", cleaned):
        suggestions.append("建议补充邮箱地址，方便招聘方快速联系。")

    phone_pattern = r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}(?!\d)"
    if not re.search(phone_pattern, cleaned):
        suggestions.append("建议补充手机号，并保持格式清晰易读。")

    link_pattern = r"(linkedin\.com|github\.com|gitlab\.com|portfolio|作品集|个人网站|领英)"
    if not re.search(link_pattern, cleaned, flags=re.IGNORECASE):
        suggestions.append("如岗位重视项目或技术能力，建议加入 LinkedIn、GitHub 或作品集链接。")

    if estimate_word_count(cleaned) < 150:
        suggestions.append("当前内容偏短，建议补充关键项目、量化成果、工具栈与职责范围。")

    outdated_terms = ["职业目标", "求职目标", "可提供推荐信", "References available upon request", "本人性格开朗"]
    found_terms = [term for term in outdated_terms if term.lower() in cleaned.lower()]
    if found_terms:
        suggestions.append(f"检测到较传统的表达：{', '.join(found_terms)}。建议改为更直接的能力摘要或成果陈述。")

    if not suggestions:
        suggestions.append("基础信息完整。下一步可以进一步强化量化成果、岗位关键词和项目影响。")
    return suggestions


def render_health_checks(text: str) -> None:
    """渲染简历健康检查面板。"""
    suggestions = resume_health_checks(text)
    with st.expander("简历健康检查", expanded=False):
        is_empty = not text.strip()
        is_clean = text.strip() and len(suggestions) == 1 and suggestions[0].startswith("基础信息完整")
        item_class = "health-ok" if is_clean else "health-item"
        for suggestion in suggestions:
            if is_empty:
                st.markdown(
                    f'<div class="notice-card">{safe_html(suggestion)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="{item_class}">{safe_html(suggestion)}</div>',
                    unsafe_allow_html=True,
                )


# =========================
# AI 提示词与调用
# =========================


def build_system_prompt(style: str, include_cover_letter: bool, include_interview: bool) -> str:
    """根据用户选择构建中文系统提示词。"""
    style_map = {
        "现代 & 亲切": "语调温暖、积极、自然，优先使用主动动词，避免夸张和空泛表达。",
        "专业 & 严谨": "正式、简洁、无冗余，以高管语气呈现判断、成果和业务价值。",
        "学术 & 规范": "强调项目成果、方法论、研究能力与结构化表达。避免使用“发表”等未经证实措辞，必要时改用“项目成果”。",
    }
    selected_style = style_map.get(style, style_map["现代 & 亲切"])
    interview_rule = (
        "必须包含 interview_questions，生成 5 个贴近 JD 的面试问题及参考答案。"
        if include_interview
        else "不要包含 interview_questions 字段。"
    )
    cover_rule = (
        "必须包含 cover_letter，生成一封完整、克制、可信的中文求职信。"
        if include_cover_letter
        else "不要包含 cover_letter 字段。"
    )

    return f"""
你是一位资深职业发展顾问、招聘策略专家和中文简历写作专家。你需要根据用户提供的原始简历和职位描述 JD，输出一份更匹配该岗位的优化简历，并给出结构化匹配分析。

整体语言风格要求：{selected_style}

重要原则：
1. 全部内容必须使用专业、流畅、自然的中文。
2. 不得虚构教育经历、公司、职级、证书、工作年限、项目成果或任何事实。
3. 可以重组、提炼、改写用户已有经历，使其更贴近 JD 的职责、技能和关键词。
4. 尽量使用量化表达，但只有在原文已有依据时才可保留或轻度改写。
5. 避免空泛套话，避免过度营销，避免明显 AI 腔。
6. 输出必须严格包含两个分隔区块，不要在分隔区块之外添加解释。

输出格式必须严格如下：

TAILORED_RESUME_START
这里输出优化后的简历，使用 Markdown 格式。结构清晰，可以包含：个人摘要、核心技能、工作经历、项目经历、教育背景、证书或补充信息。请突出匹配技能、经验和关键词。
TAILORED_RESUME_END

ANALYTICS_START
这里输出一个合法 JSON 对象，不要使用 Markdown 代码块，不要添加注释，不要使用尾随逗号。字段如下：
{{
  "match_score": 0-100 的整数,
  "skill_match_score": 0-100 的整数,
  "experience_match_score": 0-100 的整数,
  "education_match_score": 0-100 的整数,
  "strengths": ["3 条突出的匹配优势"],
  "missing_skills": ["3 条 JD 要求但简历中缺乏或较弱的技能"],
  "learning_path": [
    {{"skill": "技能名", "resources": ["资源名称 + URL", "资源名称 + URL"]}}
  ],
  "summary": "2 句鼓励性的匹配总结。",
  "interview_questions": [
    {{"question": "问题", "answer": "参考答案"}}
  ],
  "cover_letter": "求职信全文，换行请使用 \\n"
}}
ANALYTICS_END

条件字段规则：
- {interview_rule}
- {cover_rule}
- learning_path 必须针对 missing_skills 中的每个技能各推荐 2 个免费学习资源，资源需要包含名称和 URL。
- summary 必须是 2 句中文，不要超过 90 个汉字。
- 分数要体现真实匹配程度，不要一律高分。
""".strip()


def build_user_prompt(resume_text: str, jd_text: str) -> str:
    """构建用户消息。"""
    return f"""
请基于以下信息完成简历优化与职位匹配分析。

【原始简历】
{resume_text}

【职位描述 JD】
{jd_text}
""".strip()


def call_ai(
    client: OpenAI,
    resume_text: str,
    jd_text: str,
    style: str,
    include_cover_letter: bool,
    include_interview: bool,
) -> str:
    """调用 DeepSeek Chat 完成分析。"""
    response = client.chat.completions.create(
        model=API_MODEL,
        messages=[
            {
                "role": "system",
                "content": build_system_prompt(style, include_cover_letter, include_interview),
            },
            {"role": "user", "content": build_user_prompt(resume_text, jd_text)},
        ],
        temperature=0.3,
        max_tokens=6000,
    )
    return response.choices[0].message.content or ""


def extract_between(text: str, start: str, end: str) -> str:
    """提取两个分隔符之间的内容。"""
    pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.DOTALL)
    match = pattern.search(text or "")
    return match.group(1).strip() if match else ""


def parse_json_block(block: str) -> tuple[dict, bool]:
    """解析模型返回的 JSON 分析块。"""
    if not block.strip():
        return {}, False

    cleaned = block.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    candidates = [cleaned]
    object_match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if object_match:
        candidates.append(object_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else {}, True
        except json.JSONDecodeError:
            continue
    return {}, False


def parse_ai_response(response_text: str) -> dict:
    """解析 AI 输出，兼容部分格式偏移。"""
    resume = extract_between(response_text, "TAILORED_RESUME_START", "TAILORED_RESUME_END")
    analytics_block = extract_between(response_text, "ANALYTICS_START", "ANALYTICS_END")
    analytics, json_ok = parse_json_block(analytics_block)

    if not resume:
        before_analytics = response_text.split("ANALYTICS_START")[0]
        resume = before_analytics.replace("TAILORED_RESUME_START", "").replace("TAILORED_RESUME_END", "").strip()

    return {
        "tailored_resume": resume.strip(),
        "analytics": analytics,
        "json_ok": json_ok,
        "raw_response": response_text,
    }


def render_api_error(error: Exception) -> None:
    """按错误类型展示中文说明。"""
    if isinstance(error, AuthenticationError):
        show_notice("认证失败：请检查 Streamlit Secrets 中的 DEEPSEEK_API_KEY 是否正确，且没有多余空格。")
    elif isinstance(error, RateLimitError):
        show_notice("请求过于频繁或额度暂时受限：请稍后重试，或检查 DeepSeek 账户额度与速率限制。")
    elif isinstance(error, APIConnectionError):
        show_notice("网络连接失败：请确认当前部署环境可以访问 DeepSeek API，并稍后重试。")
    elif isinstance(error, APIError):
        show_notice("模型服务暂时不可用：请稍后重试，或在 DeepSeek 控制台检查服务状态。")
    else:
        show_notice("分析过程中出现异常：请稍后重试，并确认输入内容没有过长或包含无法识别的格式。")


# =========================
# PDF 与下载
# =========================


@st.cache_resource(show_spinner=False)
def resolve_chinese_font() -> tuple[str, str]:
    """查找或下载可用于中文 PDF 的字体。"""
    local_candidates = [
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/msyh.ttf"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
    ]
    for candidate in local_candidates:
        if candidate.exists():
            return str(candidate), ""

    target = Path(tempfile.gettempdir()) / "NotoSansSC-VF.ttf"
    if target.exists() and target.stat().st_size > 1024 * 100:
        return str(target), ""

    font_urls = [
        "https://github.com/googlefonts/noto-cjk/raw/main/Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf",
        "https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf",
    ]
    for url in font_urls:
        try:
            with urllib.request.urlopen(url, timeout=12) as response:
                data = response.read()
            if len(data) > 1024 * 100:
                target.write_bytes(data)
                return str(target), ""
        except Exception:
            continue

    return "", "未能自动获取中文字体，PDF 将降级为默认英文字体。中文内容可能无法完整显示，建议优先下载 Markdown。"


def markdown_to_plain_text(markdown_text: str) -> str:
    """将 Markdown 简化为适合 PDF 的纯文本。"""
    text = markdown_text or ""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def create_pdf_bytes(title: str, content: str) -> tuple[bytes | None, str]:
    """生成 PDF 字节流，失败时返回提示。"""
    font_path, font_warning = resolve_chinese_font()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_name = "Arial"
    can_render_chinese = False
    if font_path:
        try:
            try:
                pdf.add_font("NotoSansSC", "", font_path, uni=True)
            except TypeError:
                pdf.add_font("NotoSansSC", "", font_path)
            font_name = "NotoSansSC"
            can_render_chinese = True
        except Exception:
            font_warning = "中文字体加载失败，PDF 将降级为默认英文字体。建议优先下载 Markdown。"

    try:
        pdf.set_font(font_name, size=16)
        pdf.multi_cell(0, 9, title if can_render_chinese else title.encode("latin-1", "replace").decode("latin-1"))
        pdf.ln(3)
        pdf.set_font(font_name, size=11)
        plain_text = markdown_to_plain_text(content)
        if not can_render_chinese:
            plain_text = plain_text.encode("latin-1", "replace").decode("latin-1")
        for paragraph in plain_text.split("\n"):
            pdf.multi_cell(0, 7, paragraph)
            if not paragraph.strip():
                pdf.ln(1)
        output = pdf.output(dest="S")
        if isinstance(output, str):
            return output.encode("latin-1"), font_warning
        return bytes(output), font_warning
    except Exception:
        return None, "中文 PDF 生成失败。请先下载 Markdown 版本，或稍后在支持中文字体的环境中重试。"


def render_downloads(markdown_name: str, markdown_content: str, pdf_title: str, pdf_file_name: str) -> None:
    """渲染 Markdown 与 PDF 下载按钮。"""
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.download_button(
            "下载 Markdown",
            data=markdown_content.encode("utf-8"),
            file_name=markdown_name,
            mime="text/markdown",
            use_container_width=True,
        )
    with col_b:
        pdf_bytes, warning = create_pdf_bytes(pdf_title, markdown_content)
        if pdf_bytes:
            st.download_button(
                "下载 PDF",
                data=pdf_bytes,
                file_name=pdf_file_name,
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("下载 PDF", disabled=True, use_container_width=True)
        if warning:
            st.caption(warning)


# =========================
# 关键词与图表
# =========================


def extract_top_keywords(jd_text: str, top_n: int = 10) -> list[tuple[str, int]]:
    """从 JD 中提取高频硬技能关键词。"""
    skills = [
        "Python",
        "SQL",
        "Excel",
        "Tableau",
        "Power BI",
        "Java",
        "JavaScript",
        "TypeScript",
        "React",
        "Vue",
        "Node.js",
        "Docker",
        "Kubernetes",
        "AWS",
        "Azure",
        "GCP",
        "Linux",
        "Git",
        "API",
        "REST",
        "GraphQL",
        "Spark",
        "Hadoop",
        "TensorFlow",
        "PyTorch",
        "scikit-learn",
        "NLP",
        "LLM",
        "AIGC",
        "机器学习",
        "深度学习",
        "数据分析",
        "数据建模",
        "数据可视化",
        "用户研究",
        "产品设计",
        "项目管理",
        "增长",
        "CRM",
        "SaaS",
        "SEO",
        "SEM",
        "风控",
        "推荐系统",
        "大模型",
        "云计算",
        "微服务",
        "自动化测试",
        "CI/CD",
    ]

    counts = {}
    lowered = jd_text.lower()
    for skill in skills:
        if re.search(r"[\u4e00-\u9fff]", skill):
            count = jd_text.count(skill)
        else:
            pattern = r"(?<![A-Za-z0-9])" + re.escape(skill.lower()) + r"(?![A-Za-z0-9])"
            count = len(re.findall(pattern, lowered))
        if count:
            counts[skill] = count

    if not counts:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.\-/]{1,}|[\u4e00-\u9fff]{2,}", jd_text)
        stopwords = {
            "岗位",
            "负责",
            "熟悉",
            "具备",
            "能力",
            "经验",
            "优先",
            "相关",
            "完成",
            "以及",
            "进行",
            "职位",
            "要求",
            "我们",
            "团队",
        }
        for token in tokens:
            normalized = token.strip()
            if normalized in stopwords or len(normalized) < 2:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1

    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:top_n]


def build_gauge(score: int) -> go.Figure:
    """构建极简半圆仪表图。"""
    color = score_color(score)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={
                "suffix": " 分",
                "font": {"size": 34, "color": "#1A1A1A", "family": FONT_STACK},
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 0,
                    "tickcolor": "rgba(0,0,0,0)",
                    "showticklabels": False,
                },
                "bar": {"color": color, "thickness": 0.18},
                "bgcolor": "#F2F2F2",
                "borderwidth": 0,
                "steps": [{"range": [0, 100], "color": "#F2F2F2"}],
            },
        )
    )
    fig.update_layout(
        height=230,
        margin=dict(l=10, r=10, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_STACK, "color": "#1A1A1A"},
    )
    return fig


def build_keyword_chart(keywords: list[tuple[str, int]]) -> go.Figure:
    """构建 Top 关键词水平条形图。"""
    labels = [item[0] for item in keywords][::-1]
    values = [item[1] for item in keywords][::-1]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color="#6F7770"),
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(260, 34 * len(labels) + 90),
        margin=dict(l=8, r=12, t=18, b=26),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_STACK, "size": 12, "color": "#1A1A1A"},
        xaxis=dict(
            showgrid=True,
            gridcolor="#F0F0F0",
            zeroline=False,
            tickfont=dict(color="#6B6B6B"),
        ),
        yaxis=dict(showgrid=False, tickfont=dict(color="#4D4D4D")),
    )
    return fig


# =========================
# 结果展示组件
# =========================


def render_metric_bar(label: str, value: int) -> None:
    """渲染细线进度条。"""
    color = score_color(value)
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-label">
                <strong>{safe_html(label)}</strong>
                <span>{value} / 100</span>
            </div>
            <div class="thin-progress">
                <div class="thin-progress-fill" style="width: {value}%; background: {color};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tags(items: list, variant: str = "") -> None:
    """渲染标签列表。"""
    if not items:
        st.caption("暂无数据。")
        return
    class_name = "tag"
    if variant == "green":
        class_name += " tag-green"
    elif variant == "amber":
        class_name += " tag-amber"

    tags = "".join(f'<span class="{class_name}">{safe_html(item)}</span>' for item in items[:8])
    st.markdown(f'<div class="tag-wrap">{tags}</div>', unsafe_allow_html=True)


def parse_resource(resource: object) -> tuple[str, str]:
    """从资源文本中解析名称与链接。"""
    if isinstance(resource, dict):
        name = resource.get("name") or resource.get("title") or resource.get("resource") or "学习资源"
        url = resource.get("url") or resource.get("link") or ""
        return str(name), str(url)

    text = str(resource or "").strip()
    match = re.search(r"https?://[^\s，,）)]+", text)
    if not match:
        return text, ""
    url = match.group(0)
    name = text.replace(url, "").strip(" -—：:，,（）()")
    return name or url, url


def render_learning_path(learning_path: list) -> None:
    """渲染学习路径推荐。"""
    if not learning_path:
        show_notice("学习路径暂时不可用。可以根据待提升技能自行补充课程、官方文档或项目练习。")
        return

    for item in learning_path:
        if not isinstance(item, dict):
            continue
        skill = item.get("skill", "待提升技能")
        resources = item.get("resources", [])
        resource_html = ""
        for resource in resources[:2]:
            name, url = parse_resource(resource)
            if url:
                resource_html += (
                    f'<li><a class="resource-link" href="{safe_html(url)}" target="_blank">'
                    f"{safe_html(name)}</a></li>"
                )
            else:
                resource_html += f"<li>{safe_html(name)}</li>"
        st.markdown(
            f"""
            <div class="learning-card">
                <div class="small-title">{safe_html(skill)}</div>
                <ul class="small-text">{resource_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_diff(original: str, tailored: str) -> None:
    """渲染原始简历与优化简历对比。"""
    with st.expander("对比原始简历", expanded=False):
        st.caption("颜色仅用于标记文本差异，方便快速定位新增、删除与调整内容。")
        diff_table = difflib.HtmlDiff(wrapcolumn=90).make_table(
            original.splitlines(),
            tailored.splitlines(),
            fromdesc="原始简历",
            todesc="优化后简历",
            context=True,
            numlines=3,
        )
        components.html(
            f'<div class="diff-wrapper">{diff_table}</div>',
            height=520,
            scrolling=True,
        )

        col_left, col_right = st.columns(2)
        with col_left:
            st.text_area("原始简历纯文本", original, height=320, disabled=True)
        with col_right:
            st.text_area("优化后简历纯文本", tailored, height=320, disabled=True)


def render_resume_tab(result: dict, original_resume: str) -> None:
    """展示优化简历。"""
    tailored_resume = result.get("tailored_resume", "").strip()
    if not tailored_resume:
        show_notice("暂未获得可展示的优化简历。请稍后重试，或适当缩短输入内容后再次分析。")
        return

    st.markdown(tailored_resume)
    st.markdown("<hr>", unsafe_allow_html=True)
    render_downloads(
        markdown_name="CareerLens_优化简历.md",
        markdown_content=tailored_resume,
        pdf_title="CareerLens 优化简历",
        pdf_file_name="CareerLens_优化简历.pdf",
    )
    render_diff(original_resume, tailored_resume)


def render_insights_tab(result: dict, jd_text: str) -> None:
    """展示匹配洞察。"""
    analytics = result.get("analytics", {}) or {}
    if not analytics:
        show_notice("分析数据暂时不可用。优化后的简历仍可正常查看和下载。")
        return

    match_score = clamp_score(analytics.get("match_score"))
    skill_score = clamp_score(analytics.get("skill_match_score"))
    experience_score = clamp_score(analytics.get("experience_match_score"))
    education_score = clamp_score(analytics.get("education_match_score"))
    summary = analytics.get("summary", "本次分析已完成。建议结合岗位重点继续强化关键词与成果表达。")

    col_left, col_right = st.columns([1, 1], gap="large")
    with col_left:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.plotly_chart(build_gauge(match_score), use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<p class="small-text">{safe_html(summary)}</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">维度拆解</div>', unsafe_allow_html=True)
        render_metric_bar("技能匹配", skill_score)
        render_metric_bar("经验匹配", experience_score)
        render_metric_bar("教育背景", education_score)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 匹配优势")
    render_tags(analytics.get("strengths", []), variant="green")

    st.markdown("### 待提升技能")
    render_tags(analytics.get("missing_skills", []), variant="amber")

    st.markdown("### JD Top 关键词")
    keywords = extract_top_keywords(jd_text)
    if keywords:
        st.plotly_chart(build_keyword_chart(keywords), use_container_width=True, config={"displayModeBar": False})
    else:
        show_notice("当前 JD 中可提取的关键词较少。建议粘贴更完整的职位描述，以获得更稳定的分析。")

    st.markdown("### 学习路径推荐")
    render_learning_path(analytics.get("learning_path", []))


def render_interview_tab(analytics: dict) -> None:
    """展示面试准备内容。"""
    questions = analytics.get("interview_questions", []) if analytics else []
    if not questions:
        show_notice("面试问题暂时不可用。请确认侧边栏已开启生成面试问题，并重新分析。")
        return

    interview_markdown_parts = ["# CareerLens 面试准备\n"]
    for index, item in enumerate(questions[:5], start=1):
        if not isinstance(item, dict):
            continue
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not question:
            continue
        with st.expander(f"问题 {index}：{question}", expanded=False):
            st.markdown(answer or "暂无参考答案。")
        interview_markdown_parts.append(f"## 问题 {index}\n\n{question}\n\n### 参考答案\n\n{answer}\n")

    st.markdown("<hr>", unsafe_allow_html=True)
    pdf_bytes, warning = create_pdf_bytes("CareerLens 面试准备", "\n".join(interview_markdown_parts))
    if pdf_bytes:
        st.download_button(
            "下载面试问题 PDF",
            data=pdf_bytes,
            file_name="CareerLens_面试准备.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.button("下载面试问题 PDF", disabled=True, use_container_width=True)
    if warning:
        st.caption(warning)


def render_cover_letter_tab(analytics: dict) -> None:
    """展示求职信内容。"""
    cover_letter = str(analytics.get("cover_letter", "") if analytics else "").strip()
    if not cover_letter:
        show_notice("求职信暂时不可用。请确认侧边栏已开启生成求职信，并重新分析。")
        return

    st.markdown(f'<div class="cover-letter">{safe_html(cover_letter)}</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    render_downloads(
        markdown_name="CareerLens_求职信.md",
        markdown_content=cover_letter,
        pdf_title="CareerLens 求职信",
        pdf_file_name="CareerLens_求职信.pdf",
    )


# =========================
# 页面结构
# =========================


def render_sidebar() -> tuple[str, bool, bool]:
    """渲染侧边栏并返回用户配置。"""
    with st.sidebar:
        st.markdown('<div class="sidebar-title">CareerLens</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-desc">根据职位描述优化简历，生成匹配洞察、面试准备与求职信。</div>',
            unsafe_allow_html=True,
        )

        with st.expander("关于", expanded=False):
            st.markdown(
                """
CareerLens 使用 Streamlit 构建界面，并通过 OpenAI 兼容接口调用 DeepSeek 的 `deepseek-chat` 模型。

隐私承诺：您的简历与职位描述仅用于本次优化请求，不会在本应用中存储。
                """.strip()
            )

        style = st.selectbox(
            "简历风格",
            ["现代 & 亲切", "专业 & 严谨", "学术 & 规范"],
            index=0,
        )
        include_cover_letter = st.toggle("生成求职信", value=True)
        include_interview = st.toggle("生成面试问题", value=True)

        st.markdown(
            f"""
            <div class="soft-card">
                <div class="small-title">模型</div>
                <p class="small-text"><code>{API_MODEL}</code>，免费且强大。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("重新开始", use_container_width=True):
            st.session_state.confirm_reset = True

        if st.session_state.confirm_reset:
            st.caption("确认后会清空当前输入与分析结果。")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("确认清空", use_container_width=True):
                    reset_workspace()
            with col_cancel:
                if st.button("取消", use_container_width=True):
                    st.session_state.confirm_reset = False
                    st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.caption("您的数据仅用于本次优化，不会存储。")

    return style, include_cover_letter, include_interview


def render_missing_key_guide() -> None:
    """展示 API Key 配置引导。"""
    st.markdown('<p class="app-title">CareerLens</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="app-subtitle">请先配置 DeepSeek API Key，然后即可开始智能简历优化与职位匹配分析。</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="notice-card">
            <div class="small-title">需要配置密钥</div>
            <p class="small-text">
                在 Streamlit Cloud 项目的 Secrets 中添加以下内容后重新运行应用：
            </p>
            <pre style="background:#F7F7F7;border:1px solid #F0F0F0;border-radius:6px;padding:0.8rem;color:#1A1A1A;">{API_KEY_NAME} = "你的 DeepSeek API Key"</pre>
            <p class="small-text">
                本应用会通过 <code>st.secrets["{API_KEY_NAME}"]</code> 读取密钥，并使用 OpenAI 兼容接口连接 DeepSeek。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """渲染页面头部与欢迎横条。"""
    top_col, close_col = st.columns([0.88, 0.12])
    with top_col:
        st.markdown(f'<p class="app-title">{APP_NAME}</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="app-subtitle">将简历与职位描述放在同一视角下，快速获得可执行的优化建议、匹配评分与面试准备材料。</p>',
            unsafe_allow_html=True,
        )
    with close_col:
        if st.session_state.welcome_visible:
            if st.button("关闭", use_container_width=True):
                st.session_state.welcome_visible = False
                st.rerun()

    if st.session_state.welcome_visible:
        st.markdown(
            """
            <div class="welcome-card">
                首次使用建议：粘贴完整简历与完整 JD，保留项目成果、工具栈、行业关键词和岗位要求。系统不会虚构经历，只会基于现有信息进行重组与强化。
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_inputs() -> bool:
    """渲染输入区，返回是否点击分析按钮。"""
    col_resume, col_jd = st.columns(2, gap="large")

    with col_resume:
        st.markdown("### 我的简历")
        uploaded_resume = st.file_uploader(
            "上传简历文件",
            type=["txt", "pdf"],
            help="支持 .txt 与可提取文本的 .pdf 文件。",
        )
        if uploaded_resume is not None:
            signature = f"{uploaded_resume.name}-{uploaded_resume.size}"
            if signature != st.session_state.uploaded_resume_signature:
                try:
                    st.session_state.resume_text = load_resume_file(uploaded_resume)
                    st.session_state.uploaded_resume_signature = signature
                    st.caption("已从文件中提取文本，可继续手动编辑。")
                except ValueError as exc:
                    show_notice(str(exc))

        st.text_area(
            "简历文本",
            key="resume_text",
            height=340,
            placeholder="请粘贴你的中文或英文简历内容，建议保留工作经历、项目经历、教育背景、技能与证书。",
            label_visibility="collapsed",
        )
        render_health_checks(st.session_state.resume_text)

    with col_jd:
        st.markdown("### 职位描述 (JD)")
        st.text_area(
            "职位描述",
            key="jd_text",
            height=380,
            placeholder="请粘贴完整职位描述，包括岗位职责、任职要求、加分项、技术栈与业务背景。",
            label_visibility="collapsed",
        )

    st.markdown("<div style='height: 0.65rem;'></div>", unsafe_allow_html=True)
    return st.button("开始智能优化与分析", type="primary", use_container_width=True)


def render_results(result: dict, original_resume: str, jd_text: str) -> None:
    """根据分析结果渲染标签页。"""
    analytics = result.get("analytics", {}) or {}
    if not result.get("json_ok"):
        show_notice("分析数据暂时不可用。系统已尽力解析优化简历，你仍可以查看和下载简历内容。")

    tab_names = ["优化简历", "匹配洞察"]
    has_interview = bool(analytics.get("interview_questions"))
    has_cover = bool(analytics.get("cover_letter"))
    if has_interview:
        tab_names.append("面试准备")
    if has_cover:
        tab_names.append("求职信")

    tabs = st.tabs(tab_names)
    with tabs[0]:
        render_resume_tab(result, original_resume)
    with tabs[1]:
        render_insights_tab(result, jd_text)

    tab_index = 2
    if has_interview:
        with tabs[tab_index]:
            render_interview_tab(analytics)
        tab_index += 1
    if has_cover:
        with tabs[tab_index]:
            render_cover_letter_tab(analytics)


# =========================
# 主流程
# =========================


def main() -> None:
    """应用入口。"""
    init_session_state()
    style, include_cover_letter, include_interview = render_sidebar()

    api_key = get_api_key()
    if not api_key:
        render_missing_key_guide()
        return

    render_header()
    analyze_clicked = render_inputs()

    if analyze_clicked:
        resume_text = st.session_state.resume_text.strip()
        jd_text = st.session_state.jd_text.strip()

        if not resume_text and not jd_text:
            show_notice("请先填写简历和职位描述，再开始分析。")
        elif not resume_text:
            show_notice("请先粘贴或上传简历内容。")
        elif not jd_text:
            show_notice("请先粘贴职位描述 JD。")
        else:
            client = create_openai_client(api_key)
            with st.spinner("正在分析简历与职位描述，请稍候..."):
                try:
                    response_text = call_ai(
                        client=client,
                        resume_text=resume_text,
                        jd_text=jd_text,
                        style=style,
                        include_cover_letter=include_cover_letter,
                        include_interview=include_interview,
                    )
                    st.session_state.analysis_result = parse_ai_response(response_text)
                except Exception as exc:
                    st.session_state.analysis_result = None
                    render_api_error(exc)

    if st.session_state.analysis_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        render_results(
            st.session_state.analysis_result,
            st.session_state.resume_text,
            st.session_state.jd_text,
        )


if __name__ == "__main__":
    main()
