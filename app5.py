# 安装依赖：
# pip install streamlit openai PyPDF2 fpdf plotly
# difflib、json、re、io、tempfile、pathlib、urllib、html 为 Python 标准库，无需额外安装。

# ============================================================
# 基础配置与依赖
# ============================================================
import difflib
import html
import io
import json
import re
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go
import PyPDF2
import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)


API_MODEL = "gpt-3.5-turbo"
API_MODEL_OPTIONS = ["gpt-3.5-turbo"]
API_BASE_URL = "https://api.vectorengine.ai/v1"
API_KEY_NAME = "API_KEY"


st.set_page_config(
    page_title="CareerLens – 智能简历优化与职位匹配分析",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="expanded",
)


# ============================================================
# 全局样式
# ============================================================
st.markdown(
    """
    <style>
    :root {
        --bg: #F9F9F9;
        --card: #FFFFFF;
        --border: #E8E8E8;
        --border-strong: #D1D1D1;
        --text: #111111;
        --muted: #555555;
        --accent: #1A1A1A;
        --accent-hover: #333333;
        --success: #4A707A;
        --warning: #B08A42;
        --danger: #A65F55;
        --tag: #F3F3F3;
    }

    html, body, [class*="css"] {
        font-family: "Inter", "Helvetica Neue", "Arial", "PingFang SC", "Microsoft YaHei", sans-serif;
        color: var(--text);
        letter-spacing: 0;
        -webkit-font-smoothing: antialiased;
        text-rendering: optimizeLegibility;
    }

    .stApp {
        background: var(--bg);
    }

    .block-container {
        max-width: 960px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--border);
    }

    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
        height: 0 !important;
    }

    [data-testid="stSidebar"] * {
        letter-spacing: 0;
    }

    h1, h2, h3 {
        color: var(--text);
        font-weight: 600;
        letter-spacing: 0;
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
        line-height: 1.4;
    }

    p, li, label, div {
        font-size: 14px;
        line-height: 1.6;
    }

    p, li {
        color: var(--text);
    }

    hr {
        border: 0;
        border-top: 1px solid var(--border);
        margin: 2rem 0;
    }

    textarea, input, [data-baseweb="textarea"] textarea, [data-baseweb="input"] input {
        background: #FFFFFF !important;
        border-radius: 6px !important;
        color: var(--text) !important;
        box-shadow: none !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }

    [data-baseweb="textarea"], [data-baseweb="input"] {
        border-color: var(--border-strong) !important;
        border-radius: 6px !important;
        box-shadow: none !important;
    }

    [data-baseweb="textarea"]:focus-within, [data-baseweb="input"]:focus-within {
        border-color: #999999 !important;
        box-shadow: none !important;
    }

    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-primary"] {
        border-radius: 6px !important;
        box-shadow: none !important;
        transition: none !important;
        font-weight: 500 !important;
        min-height: 2.5rem;
    }

    [data-testid="stBaseButton-primary"] {
        background: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        color: #FFFFFF !important;
    }

    [data-testid="stBaseButton-primary"]:hover {
        background: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
        color: #FFFFFF !important;
    }

    [data-testid="stBaseButton-secondary"],
    .stDownloadButton > button {
        background: #FFFFFF !important;
        border: 1px solid var(--border-strong) !important;
        color: var(--text) !important;
    }

    [data-testid="stBaseButton-secondary"]:hover,
    .stDownloadButton > button:hover {
        border-color: #CFCFCF !important;
        color: var(--text) !important;
    }

    button:focus, button:active {
        box-shadow: none !important;
        outline: none !important;
    }

    [data-testid="stFileUploader"] section {
        background: #FFFFFF !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }

    [data-testid="stFileUploader"] section button {
        border-radius: 6px !important;
        box-shadow: none !important;
    }

    [data-testid="stFileUploaderDropzone"] [data-testid="stIconMaterial"] {
        display: none !important;
    }

    [data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p {
        display: none !important;
    }

    [data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"]::after {
        content: "选择文件";
        font-size: 14px !important;
        line-height: 1.4;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] span {
        display: none !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"]::after {
        content: "单个文件上限 200MB · TXT、PDF";
        color: var(--muted);
        font-size: 12px !important;
        line-height: 1.5;
    }

    [data-testid="stExpander"] {
        background: #FFFFFF;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
        overflow: hidden;
    }

    [data-testid="stExpander"] details {
        border-radius: 8px !important;
    }

    [data-testid="stTabs"] [role="tablist"] {
        gap: 0.25rem;
        border-bottom: 1px solid var(--border);
    }

    [data-testid="stTabs"] [role="tab"] {
        border-radius: 6px 6px 0 0;
        color: var(--muted);
        padding: 0.75rem 0.9rem;
        font-weight: 500;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--text);
        border-bottom: 2px solid var(--accent);
    }

    .app-subtitle {
        color: var(--muted);
        margin: 0 0 1.5rem 0;
        font-size: 15px;
    }

    .section-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        padding: 1.5rem;
        margin: 1rem 0 1.5rem 0;
    }

    .welcome-card,
    .api-card {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 8px;
        color: var(--muted);
        padding: 1rem 1.25rem;
        margin: 1rem 0 1.25rem 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    .notice-card {
        background: #FFF9E8;
        border: 1px solid #EFE2C0;
        border-radius: 8px;
        color: #555555;
        padding: 1rem 1.25rem;
        margin: 1rem 0 1.25rem 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    .api-card strong,
    .notice-card strong,
    .welcome-card strong {
        color: var(--text);
        font-weight: 600;
    }

    .health-card {
        background: #FBF7EF;
        border-left: 3px solid var(--warning);
        border-radius: 6px;
        color: #5C4A2C;
        padding: 0.75rem 0.85rem;
        margin: 0.55rem 0;
    }

    .health-card.ok {
        background: #F1F7F4;
        border-left-color: var(--success);
        color: #285544;
    }

    .tag {
        display: inline-flex;
        align-items: center;
        background: var(--tag);
        color: #4D4D4D;
        border-radius: 20px;
        padding: 0.28rem 0.65rem;
        margin: 0.2rem 0.3rem 0.2rem 0;
        font-size: 12px;
        line-height: 1.4;
        white-space: normal;
    }

    .tag.good {
        background: #EDF5F1;
        color: #245C48;
    }

    .tag.missing {
        background: #F8F1EF;
        color: #7A3F35;
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        margin-bottom: 0.75rem;
    }

    .score-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.45rem;
        color: var(--text);
    }

    .score-row span {
        color: var(--muted);
    }

    .score-row strong {
        color: var(--text);
        font-weight: 600;
    }

    .meter {
        width: 100%;
        height: 5px;
        background: #F1F1F1;
        border-radius: 999px;
        overflow: hidden;
    }

    .meter > div {
        height: 5px;
        border-radius: 999px;
    }

    .resource-card {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    .resource-card h4 {
        margin: 0 0 0.5rem 0;
        font-size: 14px;
        font-weight: 600;
        color: var(--text);
    }

    .resource-card a {
        color: var(--accent);
        text-decoration: none;
        border-bottom: 1px solid #D8D8D8;
    }

    .resource-card a:hover {
        color: var(--accent-hover);
        border-bottom-color: var(--accent-hover);
    }

    .markdown-body {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }

    .small-muted {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
    }

    .sidebar-badge {
        display: inline-block;
        background: #F3F3F3;
        color: #4D4D4D;
        border-radius: 20px;
        padding: 0.25rem 0.65rem;
        font-size: 12px;
        margin-top: 0.25rem;
    }

    a {
        color: var(--accent);
        text-decoration: none;
    }

    a:hover {
        color: var(--accent-hover);
        text-decoration: none;
    }

    @media (max-width: 760px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1 {
            font-size: 1.55rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 状态管理
# ============================================================
def init_session_state() -> None:
    """初始化页面所需的会话状态。"""
    defaults = {
        "resume_text": "",
        "jd_text": "",
        "tailored_resume": "",
        "analytics": None,
        "raw_response": "",
        "analysis_warning": "",
        "uploaded_resume_name": "",
        "show_welcome": True,
        "confirm_reset": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_workspace() -> None:
    """清空当前页面的所有输入与分析结果。"""
    keys = [
        "resume_text",
        "jd_text",
        "tailored_resume",
        "analytics",
        "raw_response",
        "analysis_warning",
        "uploaded_resume_name",
        "confirm_reset",
    ]
    for key in keys:
        if key in st.session_state:
            if key == "analytics":
                st.session_state[key] = None
            else:
                st.session_state[key] = ""
    st.session_state["confirm_reset"] = False


init_session_state()


# ============================================================
# API 接入
# ============================================================
def get_api_key() -> Optional[str]:
    """从 Streamlit Secrets 中读取第三方 API 密钥。"""
    try:
        value = st.secrets[API_KEY_NAME]
        if value and str(value).strip():
            return str(value).strip()
    except Exception:
        return None
    return None


@st.cache_resource(show_spinner=False)
def get_openai_client(api_key: str) -> OpenAI:
    """创建 OpenAI 兼容客户端。"""
    return OpenAI(api_key=api_key, base_url=API_BASE_URL)


def explain_api_error(error: Exception) -> str:
    """将常见 API 异常转换为中文提示。"""
    if isinstance(error, AuthenticationError):
        return f"认证失败：请检查 Streamlit Secrets 中的 {API_KEY_NAME} 是否正确，且账号额度或权限可用。"
    if isinstance(error, RateLimitError):
        return "请求过于频繁：当前模型服务触发了速率限制。请稍后重试，或减少连续分析次数。"
    if isinstance(error, (APITimeoutError, APIConnectionError)):
        return "连接失败：暂时无法连接到第三方模型转发服务。请检查网络状态，稍后再次尝试。"
    if isinstance(error, APIError):
        return f"模型服务暂时不可用：{str(error)}"
    return f"分析过程中出现异常：{str(error)}"


# ============================================================
# 文本提取与简历健康检查
# ============================================================
def extract_text_from_upload(uploaded_file: Any) -> str:
    """从 txt 或 pdf 文件中提取简历文本。"""
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        raw_bytes = uploaded_file.getvalue()
        for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
            try:
                return raw_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw_bytes.decode("utf-8", errors="ignore")

    if file_name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text.strip())
        return "\n\n".join(pages)

    return ""


def count_words_like_units(text: str) -> int:
    """估算中文与英文混合简历的字词规模。"""
    latin_words = re.findall(r"[A-Za-z][A-Za-z0-9_+#.\-]*", text)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    return len(latin_words) + max(1, len(chinese_chars) // 2) if text.strip() else 0


def build_resume_health_checks(text: str) -> List[Tuple[str, bool]]:
    """生成简历健康检查建议。"""
    normalized = text.strip()
    if not normalized:
        return [("粘贴或上传简历后，这里会显示基础完整性检查。", False)]

    checks: List[Tuple[str, bool]] = []
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", normalized))
    has_phone = bool(
        re.search(r"(\+?\d[\d\s\-()]{7,}\d)|((?:\+?86)?1[3-9]\d{9})", normalized)
    )
    has_profile_link = bool(
        re.search(r"(linkedin\.com|github\.com|gitlab\.com|portfolio|个人主页|作品集)", normalized, re.I)
    )
    word_units = count_words_like_units(normalized)
    outdated_terms = [
        "目标",
        "职业目标",
        "可提供推荐信",
        "references available upon request",
        "objective",
    ]
    matched_outdated = [term for term in outdated_terms if term.lower() in normalized.lower()]

    if has_email:
        checks.append(("已包含邮箱，招聘方可以快速联系你。", True))
    else:
        checks.append(("建议补充专业邮箱，放在简历顶部的联系信息中。", False))

    if has_phone:
        checks.append(("已包含手机号，基础联系信息较完整。", True))
    else:
        checks.append(("建议补充手机号，并保持格式清晰统一。", False))

    if has_profile_link:
        checks.append(("已包含领英、GitHub 或作品集链接，有助于补充能力证明。", True))
    else:
        checks.append(("如适用，建议加入领英、GitHub 或作品集链接，增强可信度。", False))

    if word_units >= 150:
        checks.append(("简历内容量基本充足，可以支撑模型进行针对性优化。", True))
    else:
        checks.append(("当前简历内容偏少，建议补充项目、职责、成果和量化影响。", False))

    if matched_outdated:
        joined_terms = "、".join(matched_outdated)
        checks.append(f"检测到可能过时的表达：{joined_terms}。建议改为更具体的职业摘要或成果描述。", False)
    else:
        checks.append(("未检测到明显过时用语，表达基础较稳妥。", True))

    return checks


def render_health_checks(text: str) -> None:
    """渲染简历健康检查面板。"""
    with st.expander("简历健康检查", expanded=False):
        for message, ok in build_resume_health_checks(text):
            css_class = "health-card ok" if ok else "health-card"
            st.markdown(
                f'<div class="{css_class}">{html.escape(message)}</div>',
                unsafe_allow_html=True,
            )


# ============================================================
# Prompt 构建与模型调用
# ============================================================
def build_system_prompt(style: str, include_cover_letter: bool, include_interview: bool) -> str:
    """根据用户选择的风格生成中文系统提示词。"""
    style_guides = {
        "现代 & 亲切": "语调温暖、积极，使用主动动词，表达自然但保持专业克制。",
        "专业 & 严谨": "正式、简洁、无冗余，采用高管汇报式语气，突出业务影响和结果。",
        "学术 & 规范": "强调项目成果、方法论、研究能力与结构化表达，避免使用“发表”等未经证实的经历描述，优先使用“项目成果”。",
    }
    selected_style = style_guides.get(style, style_guides["现代 & 亲切"])

    interview_instruction = (
        '必须包含 "interview_questions" 字段，生成 5 个面试问题及参考答案，格式为 '
        '[{"question": "...", "answer": "..."}]。'
        if include_interview
        else '不要包含 "interview_questions" 字段。'
    )
    cover_letter_instruction = (
        '必须包含 "cover_letter" 字段，生成一封完整求职信，语气专业、自然、具体。'
        if include_cover_letter
        else '不要包含 "cover_letter" 字段。'
    )

    return f"""
你是一位资深职业顾问、招聘专家和中文简历编辑。你的任务是根据候选人的原始简历与职位描述 JD，输出一份更匹配该岗位的优化简历，并提供结构化匹配分析。

写作风格：
{selected_style}

核心原则：
1. 所有内容必须使用中文。
2. 不得虚构候选人没有提供的经历、学历、公司、证书、项目、技能或成果。
3. 可以在不改变事实的前提下重写表达、强化关键词、调整结构、突出与 JD 高相关的经历。
4. 如果原始简历缺少关键事实，请保守表达，不要编造。
5. 优化后的简历使用 Markdown 格式，结构清晰，适合直接复制到文档中。
6. JSON 必须是严格合法 JSON，不要使用注释，不要使用 Markdown 代码块。

你必须严格按以下分隔符输出，不得省略或改名：

TAILORED_RESUME_START
这里放优化后的 Markdown 简历
TAILORED_RESUME_END

ANALYTICS_START
{{
  "match_score": 0,
  "skill_match_score": 0,
  "experience_match_score": 0,
  "education_match_score": 0,
  "strengths": ["优势1", "优势2", "优势3"],
  "missing_skills": ["缺失技能1", "缺失技能2", "缺失技能3"],
  "learning_path": [
    {{"skill": "技能名", "resources": ["资源名称 + URL", "资源名称 + URL"]}}
  ],
  "summary": "用 2 句鼓励性的中文总结说明匹配情况。"
}}
ANALYTICS_END

JSON 字段要求：
- match_score：总分，0 到 100 的整数。
- skill_match_score：技能匹配分，0 到 100 的整数。
- experience_match_score：经验匹配分，0 到 100 的整数。
- education_match_score：教育背景匹配分，0 到 100 的整数。
- strengths：3 条突出的匹配优势。
- missing_skills：3 条 JD 要求但简历中缺乏的技能。
- learning_path：针对每个缺失技能推荐 2 个免费学习资源，资源必须包含名称和 URL。
- summary：2 句鼓励性的匹配总结。
- {interview_instruction}
- {cover_letter_instruction}

请保证分隔符之外不要输出额外解释。
""".strip()


def call_model(
    client: OpenAI,
    model_name: str,
    resume_text: str,
    jd_text: str,
    style: str,
    include_cover_letter: bool,
    include_interview: bool,
) -> str:
    """调用第三方 OpenAI 兼容接口生成优化结果。"""
    system_prompt = build_system_prompt(style, include_cover_letter, include_interview)
    user_prompt = f"""
请基于以下材料完成简历优化与职位匹配分析。

【原始简历】
{resume_text}

【职位描述 JD】
{jd_text}
""".strip()

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.35,
        max_tokens=5200,
    )
    return response.choices[0].message.content or ""


def extract_between(text: str, start_marker: str, end_marker: str) -> str:
    """按分隔符提取模型输出片段。"""
    pattern = re.escape(start_marker) + r"(.*?)" + re.escape(end_marker)
    match = re.search(pattern, text, flags=re.S)
    if not match:
        return ""
    return match.group(1).strip()


def parse_analytics(raw_json: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """解析模型返回的 JSON 分析块，失败时返回提示。"""
    if not raw_json.strip():
        return None, "分析数据暂时不可用：模型没有返回结构化 JSON。"

    cleaned = raw_json.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.I).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first >= 0 and last > first:
        cleaned = cleaned[first : last + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return None, "分析数据暂时不可用：JSON 解析失败，但优化简历仍可正常查看。"

    return data, ""


def parse_model_response(raw_response: str) -> Tuple[str, Optional[Dict[str, Any]], str]:
    """解析模型完整输出。"""
    tailored_resume = extract_between(
        raw_response, "TAILORED_RESUME_START", "TAILORED_RESUME_END"
    )
    analytics_raw = extract_between(raw_response, "ANALYTICS_START", "ANALYTICS_END")
    analytics, warning = parse_analytics(analytics_raw)

    if not tailored_resume:
        tailored_resume = raw_response.strip()
        if not warning:
            warning = "模型没有按预期返回分隔符，已尝试展示完整文本。"

    return tailored_resume, analytics, warning


# ============================================================
# PDF 与下载工具
# ============================================================
FONT_URLS = [
    (
        "NotoSansSC-VF.ttf",
        "https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf",
    ),
]


def markdown_to_plain_text(markdown_text: str) -> str:
    """将 Markdown 内容转换为适合 PDF 的纯文本。"""
    text = markdown_text
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1（\2）", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "• ", text, flags=re.M)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def find_local_chinese_font() -> Optional[Path]:
    """查找常见系统中文字体。"""
    candidates = [
        Path("C:/Windows/Fonts/msyh.ttf"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/arphic/uming.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


@st.cache_data(show_spinner=False)
def download_chinese_font() -> str:
    """下载开源中文字体并返回本地路径；失败时返回空字符串。"""
    font_dir = Path(tempfile.gettempdir()) / "careerlens_fonts"
    font_dir.mkdir(parents=True, exist_ok=True)

    for file_name, url in FONT_URLS:
        target = font_dir / file_name
        if target.exists() and target.stat().st_size > 1024:
            return str(target)
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "CareerLens Streamlit App"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                target.write_bytes(response.read())
            if target.exists() and target.stat().st_size > 1024:
                return str(target)
        except Exception:
            continue

    return ""


def add_chinese_font(pdf: FPDF) -> Tuple[bool, str]:
    """为 PDF 注册中文字体，失败时允许降级。"""
    candidates: List[Path] = []
    local_font = find_local_chinese_font()
    if local_font:
        candidates.append(local_font)

    downloaded = download_chinese_font()
    if downloaded:
        candidates.append(Path(downloaded))

    for font_path in candidates:
        try:
            try:
                pdf.add_font("CareerlensCN", "", str(font_path), uni=True)
            except TypeError:
                pdf.add_font("CareerlensCN", "", str(font_path))
            pdf.set_font("CareerlensCN", size=11)
            return True, ""
        except Exception:
            continue

    pdf.set_font("Helvetica", size=11)
    return False, "未能加载中文字体，PDF 将降级为默认英文字体。建议优先下载 Markdown 版本保存中文内容。"


def normalize_pdf_text(text: str, has_chinese_font: bool) -> str:
    """在无中文字体时避免 PDF 输出报错。"""
    if has_chinese_font:
        return text
    return text.encode("latin-1", errors="replace").decode("latin-1")


def make_pdf(title: str, content: str) -> Tuple[Optional[bytes], str]:
    """生成 PDF 字节流。"""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        has_chinese_font, warning = add_chinese_font(pdf)

        title_text = normalize_pdf_text(title, has_chinese_font)
        body_text = normalize_pdf_text(markdown_to_plain_text(content), has_chinese_font)

        pdf.set_font(pdf.font_family, style="", size=15)
        pdf.multi_cell(0, 9, title_text)
        pdf.ln(3)
        pdf.set_font(pdf.font_family, style="", size=11)

        for paragraph in body_text.split("\n"):
            line = paragraph.strip()
            if not line:
                pdf.ln(3)
                continue
            pdf.multi_cell(0, 7, line)

        output = pdf.output(dest="S")
        if isinstance(output, str):
            return output.encode("latin-1"), warning
        return bytes(output), warning
    except Exception as error:
        return None, f"中文 PDF 生成失败：{error}。请先下载 Markdown 版本。"


def make_interview_markdown(items: List[Dict[str, str]]) -> str:
    """将面试问题列表转换为 Markdown。"""
    blocks = ["# 面试准备问题\n"]
    for index, item in enumerate(items, start=1):
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        blocks.append(f"## {index}. {question}\n\n{answer}\n")
    return "\n".join(blocks).strip()


def render_downloads(base_name: str, title: str, content: str, include_markdown: bool = True) -> None:
    """渲染 Markdown 与 PDF 下载按钮。"""
    pdf_bytes, pdf_warning = make_pdf(title, content)

    if include_markdown:
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "下载 Markdown",
                data=content.encode("utf-8"),
                file_name=f"{base_name}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_b:
            if pdf_bytes:
                st.download_button(
                    "下载 PDF",
                    data=pdf_bytes,
                    file_name=f"{base_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.button("下载 PDF", disabled=True, use_container_width=True)
    else:
        if pdf_bytes:
            st.download_button(
                "下载 PDF",
                data=pdf_bytes,
                file_name=f"{base_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("下载 PDF", disabled=True, use_container_width=True)

    if pdf_warning:
        st.markdown(
            f'<div class="small-muted">{html.escape(pdf_warning)}</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# 匹配洞察与图表
# ============================================================
def clamp_score(value: Any) -> int:
    """将分数限制在 0 到 100。"""
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        number = 0
    return max(0, min(100, number))


def score_color(score: int) -> str:
    """根据分数返回低饱和度状态色。"""
    if score >= 75:
        return "#4A707A"
    if score >= 50:
        return "#8E9EAB"
    return "#A65F55"


def render_gauge(score: int) -> None:
    """渲染极简半圆仪表图。"""
    color = score_color(score)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 30, "color": "#1A1A1A"}},
            gauge={
                "axis": {"range": [0, 100], "visible": False},
                "bar": {"color": color, "thickness": 0.22},
                "bgcolor": "#F1F1F1",
                "borderwidth": 0,
                "shape": "angular",
            },
            domain={"x": [0, 1], "y": [0, 1]},
        )
    )
    fig.update_layout(
        height=230,
        margin=dict(l=20, r=20, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Helvetica Neue, Arial, Microsoft YaHei, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_score_line(label: str, score: int) -> None:
    """渲染细线进度条。"""
    color = score_color(score)
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="score-row">
                <span>{html.escape(label)}</span>
                <strong>{score}/100</strong>
            </div>
            <div class="meter"><div style="width: {score}%; background: {color};"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tags(items: List[Any], css_class: str) -> None:
    """渲染标签列表。"""
    if not items:
        st.markdown('<span class="tag">暂无数据</span>', unsafe_allow_html=True)
        return
    tags = "".join(
        f'<span class="tag {css_class}">{html.escape(str(item))}</span>' for item in items
    )
    st.markdown(tags, unsafe_allow_html=True)


HARD_SKILL_PATTERNS = [
    "Python",
    "SQL",
    "R",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "Node.js",
    "Django",
    "Flask",
    "FastAPI",
    "Spring",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "GCP",
    "Linux",
    "Git",
    "CI/CD",
    "Spark",
    "Hadoop",
    "Kafka",
    "Airflow",
    "Tableau",
    "Power BI",
    "Excel",
    "机器学习",
    "深度学习",
    "自然语言处理",
    "数据分析",
    "数据建模",
    "数据可视化",
    "项目管理",
    "产品分析",
    "A/B 测试",
    "用户研究",
    "需求分析",
    "增长",
    "CRM",
    "ERP",
    "SaaS",
    "LLM",
    "Prompt",
    "API",
]


def extract_top_keywords(jd_text: str, limit: int = 10) -> List[Tuple[str, int]]:
    """从 JD 中启发式提取高频硬技能关键词。"""
    counts: Dict[str, int] = {}
    lower_jd = jd_text.lower()
    for keyword in HARD_SKILL_PATTERNS:
        escaped = re.escape(keyword.lower())
        if re.search(r"[\u4e00-\u9fff]", keyword):
            count = lower_jd.count(keyword.lower())
        else:
            count = len(re.findall(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", lower_jd))
        if count > 0:
            counts[keyword] = count

    if not counts:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{2,}", jd_text)
        stopwords = {
            "and",
            "the",
            "with",
            "for",
            "you",
            "our",
            "are",
            "this",
            "that",
            "from",
            "will",
            "have",
            "more",
            "team",
            "work",
            "role",
        }
        for token in tokens:
            normalized = token.strip(".,;:()[]{}").lower()
            if normalized and normalized not in stopwords:
                counts[token.strip(".,;:()[]{}")] = counts.get(token.strip(".,;:()[]{}"), 0) + 1

    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]


def render_keyword_chart(jd_text: str) -> None:
    """渲染 Top 关键词水平条形图。"""
    keywords = extract_top_keywords(jd_text)
    if not keywords:
        st.markdown(
            '<div class="notice-card">暂未从 JD 中识别到足够明确的硬技能关键词。</div>',
            unsafe_allow_html=True,
        )
        return

    labels = [item[0] for item in keywords]
    values = [item[1] for item in keywords]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color="#2C3E50"),
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(260, 34 * len(labels)),
        margin=dict(l=10, r=20, t=10, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, Helvetica Neue, Arial, Microsoft YaHei, sans-serif",
            color="#1A1A1A",
            size=12,
        ),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(autorange="reversed", showgrid=False, zeroline=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def split_resource(resource: str) -> Tuple[str, str]:
    """从资源字符串中提取名称和 URL。"""
    text = str(resource).strip()
    match = re.search(r"(https?://\S+)", text)
    if not match:
        return text, ""
    url = match.group(1).rstrip("，。,)")
    name = text.replace(match.group(1), "").strip(" -—:：，,")
    return name or url, url


def render_learning_path(learning_path: List[Dict[str, Any]]) -> None:
    """渲染学习路径卡片。"""
    if not learning_path:
        st.markdown(
            '<div class="notice-card">暂未生成学习路径。你可以重新分析，或在简历中补充更具体的技能背景。</div>',
            unsafe_allow_html=True,
        )
        return

    for item in learning_path:
        skill = html.escape(str(item.get("skill", "待提升技能")))
        resources = item.get("resources", [])
        links = []
        for resource in resources[:2]:
            name, url = split_resource(str(resource))
            safe_name = html.escape(name)
            safe_url = html.escape(url, quote=True)
            if url:
                links.append(f'<li><a href="{safe_url}" target="_blank">{safe_name}</a></li>')
            else:
                links.append(f"<li>{safe_name}</li>")
        resource_html = "".join(links) if links else "<li>暂无资源链接</li>"
        st.markdown(
            f"""
            <div class="resource-card">
                <h4>{skill}</h4>
                <ul>{resource_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 差异对比
# ============================================================
def render_diff(original: str, tailored: str) -> None:
    """渲染 HTML 差异对比与纯文本并排视图。"""
    with st.expander("对比原始简历", expanded=False):
        diff_html = difflib.HtmlDiff(wrapcolumn=80).make_table(
            original.splitlines(),
            tailored.splitlines(),
            fromdesc="原始简历",
            todesc="优化简历",
            context=True,
            numlines=3,
        )
        components.html(
            f"""
            <html>
            <head>
            <style>
            body {{
                margin: 0;
                font-family: Inter, Helvetica Neue, Arial, Microsoft YaHei, sans-serif;
                color: #1A1A1A;
                background: #FFFFFF;
            }}
            table.diff {{
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
                line-height: 1.5;
            }}
            .diff_header {{
                background: #F5F5F5;
                color: #4D4D4D;
                font-weight: 600;
                padding: 6px;
                border: 1px solid #F0F0F0;
            }}
            td {{
                vertical-align: top;
                border: 1px solid #F0F0F0;
                padding: 5px 6px;
            }}
            .diff_add {{ background: #EDF5F1; }}
            .diff_chg {{ background: #FBF7EF; }}
            .diff_sub {{ background: #F8F1EF; }}
            a {{ color: #2C2C2C; text-decoration: none; }}
            </style>
            </head>
            <body>{diff_html}</body>
            </html>
            """,
            height=460,
            scrolling=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.text_area("原始简历纯文本", value=original, height=300, disabled=True)
        with col_b:
            st.text_area("优化简历纯文本", value=tailored, height=300, disabled=True)


# ============================================================
# 页面片段
# ============================================================
def render_api_key_guide() -> None:
    """渲染密钥配置引导。"""
    st.markdown(
        f"""
        <div class="api-card">
            <strong>需要配置 API_KEY 后才能开始分析。</strong><br>
            在 Streamlit Cloud 中打开应用设置，进入 Secrets，添加以下内容：<br>
            <code>{API_KEY_NAME} = "你的第三方 API Key"</code><br>
            保存后重新运行应用即可。密钥只会用于本次模型转发请求，不会在页面中展示，也不会写入源码。
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_notice(message: str) -> None:
    """渲染温和提示卡片。"""
    st.markdown(
        f'<div class="notice-card">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar() -> Tuple[str, bool, bool, str]:
    """渲染侧边栏并返回用户配置。"""
    with st.sidebar:
        st.markdown("### CareerLens")
        st.markdown(
            '<div class="small-muted">智能简历优化与职位匹配分析工具。</div>',
            unsafe_allow_html=True,
        )

        with st.expander("关于", expanded=False):
            st.markdown(
                """
                CareerLens 使用 Streamlit 构建界面，通过 VectorEngine 的 OpenAI 兼容接口调用第三方平台支持的模型，帮助你根据 JD 优化简历、分析匹配度、准备面试并生成求职信。

                隐私承诺：你的数据仅用于本次优化请求，不会由本应用存储。
                """
            )

        style = st.selectbox(
            "简历风格",
            ["现代 & 亲切", "专业 & 严谨", "学术 & 规范"],
            index=0,
        )
        include_cover_letter = st.toggle("生成求职信", value=True)
        include_interview = st.toggle("生成面试问题", value=True)

        selected_model = st.selectbox(
            "模型",
            API_MODEL_OPTIONS,
            index=API_MODEL_OPTIONS.index(API_MODEL),
            help="当前仅保留第三方平台支持的 gpt-3.5-turbo，可在文件顶部常量中扩展。",
        )
        st.markdown('<span class="sidebar-badge">OpenAI 兼容接口 · VectorEngine</span>', unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("重新开始", use_container_width=True):
            st.session_state["confirm_reset"] = True

        if st.session_state.get("confirm_reset"):
            st.markdown(
                '<div class="small-muted">再次点击确认清空当前输入与分析结果。</div>',
                unsafe_allow_html=True,
            )
            if st.button("确认清空", use_container_width=True):
                reset_workspace()
                st.rerun()
            if st.button("取消", use_container_width=True):
                st.session_state["confirm_reset"] = False
                st.rerun()

        st.markdown(
            '<div class="small-muted">您的数据仅用于本次优化，不会存储。</div>',
            unsafe_allow_html=True,
        )

    return style, include_cover_letter, include_interview, selected_model


def render_inputs() -> Tuple[str, str, bool]:
    """渲染简历和 JD 输入区。"""
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown("### 我的简历")
        uploaded_resume = st.file_uploader(
            "上传简历文件",
            type=["txt", "pdf"],
            help="支持 .txt 与 .pdf。上传后会自动提取文本并填入下方文本框。",
        )
        if uploaded_resume and uploaded_resume.name != st.session_state["uploaded_resume_name"]:
            try:
                extracted_text = extract_text_from_upload(uploaded_resume)
                if extracted_text.strip():
                    st.session_state["resume_text"] = extracted_text.strip()
                    st.session_state["uploaded_resume_name"] = uploaded_resume.name
                    st.success("已从文件中提取简历文本。")
                else:
                    st.warning("未能从文件中提取到有效文本，请尝试直接粘贴简历内容。")
            except Exception as error:
                st.warning(f"文件解析失败：{error}")

        resume_text = st.text_area(
            "简历文本",
            key="resume_text",
            height=340,
            placeholder="请粘贴你的中文或英文简历内容。建议包含联系方式、职业摘要、工作经历、项目经历、教育背景和技能。",
            label_visibility="collapsed",
        )
        render_health_checks(resume_text)

    with col_right:
        st.markdown("### 职位描述 (JD)")
        jd_text = st.text_area(
            "职位描述",
            key="jd_text",
            height=380,
            placeholder="请粘贴目标岗位的完整 JD，包括职责、任职要求、加分项和团队背景。",
            label_visibility="collapsed",
        )

    st.markdown("")
    should_analyze = st.button(
        "开始智能优化与分析",
        type="primary",
        use_container_width=True,
    )
    return resume_text, jd_text, should_analyze


def render_resume_tab(tailored_resume: str, original_resume: str) -> None:
    """渲染优化简历标签页。"""
    st.markdown("### 优化简历")
    with st.container(border=True):
        st.markdown(tailored_resume)
    st.markdown("")
    render_downloads("careerlens_优化简历", "CareerLens 优化简历", tailored_resume)
    render_diff(original_resume, tailored_resume)


def render_insights_tab(analytics: Optional[Dict[str, Any]], jd_text: str) -> None:
    """渲染匹配洞察标签页。"""
    st.markdown("### 匹配洞察")
    if not analytics:
        render_notice("分析数据暂时不可用。你仍然可以查看和下载优化后的简历。")
        render_keyword_chart(jd_text)
        return

    match_score = clamp_score(analytics.get("match_score"))
    skill_score = clamp_score(analytics.get("skill_match_score"))
    experience_score = clamp_score(analytics.get("experience_match_score"))
    education_score = clamp_score(analytics.get("education_match_score"))
    summary = str(analytics.get("summary", "")).strip()

    col_left, col_right = st.columns([1, 1], gap="large")
    with col_left:
        render_gauge(match_score)
        if summary:
            st.markdown(
                f'<div class="small-muted">{html.escape(summary)}</div>',
                unsafe_allow_html=True,
            )
    with col_right:
        render_score_line("技能匹配", skill_score)
        render_score_line("经验匹配", experience_score)
        render_score_line("教育背景", education_score)

    st.markdown("#### 匹配优势")
    render_tags(analytics.get("strengths", []), "good")

    st.markdown("#### 待提升技能")
    render_tags(analytics.get("missing_skills", []), "missing")

    st.markdown("#### Top 关键词")
    render_keyword_chart(jd_text)

    st.markdown("#### 学习路径推荐")
    learning_path = analytics.get("learning_path", [])
    render_learning_path(learning_path if isinstance(learning_path, list) else [])


def render_interview_tab(analytics: Optional[Dict[str, Any]]) -> None:
    """渲染面试准备标签页。"""
    st.markdown("### 面试准备")
    questions = []
    if analytics:
        raw_questions = analytics.get("interview_questions", [])
        if isinstance(raw_questions, list):
            questions = raw_questions

    if not questions:
        render_notice("暂未生成面试问题。请确认侧边栏已开启“生成面试问题”，然后重新分析。")
        return

    for index, item in enumerate(questions[:5], start=1):
        question = str(item.get("question", f"问题 {index}")).strip()
        answer = str(item.get("answer", "")).strip()
        with st.expander(f"{index}. {question}", expanded=False):
            st.markdown(answer or "暂无参考答案。")

    markdown_content = make_interview_markdown(questions[:5])
    render_downloads(
        "careerlens_面试问题",
        "CareerLens 面试准备",
        markdown_content,
        include_markdown=False,
    )


def render_cover_letter_tab(analytics: Optional[Dict[str, Any]]) -> None:
    """渲染求职信标签页。"""
    st.markdown("### 求职信")
    cover_letter = ""
    if analytics:
        cover_letter = str(analytics.get("cover_letter", "")).strip()

    if not cover_letter:
        render_notice("暂未生成求职信。请确认侧边栏已开启“生成求职信”，然后重新分析。")
        return

    with st.container(border=True):
        st.markdown(cover_letter)
    st.markdown("")
    render_downloads("careerlens_求职信", "CareerLens 求职信", cover_letter)


def render_results(include_cover_letter: bool, include_interview: bool) -> None:
    """根据结果和开关动态渲染标签页。"""
    tailored_resume = st.session_state.get("tailored_resume", "")
    if not tailored_resume:
        return

    warning = st.session_state.get("analysis_warning", "")
    if warning:
        render_notice(warning)

    labels = ["优化简历", "匹配洞察"]
    if include_interview:
        labels.append("面试准备")
    if include_cover_letter:
        labels.append("求职信")

    tabs = st.tabs(labels)
    tab_map = dict(zip(labels, tabs))

    with tab_map["优化简历"]:
        render_resume_tab(tailored_resume, st.session_state.get("resume_text", ""))

    with tab_map["匹配洞察"]:
        render_insights_tab(st.session_state.get("analytics"), st.session_state.get("jd_text", ""))

    if include_interview and "面试准备" in tab_map:
        with tab_map["面试准备"]:
            render_interview_tab(st.session_state.get("analytics"))

    if include_cover_letter and "求职信" in tab_map:
        with tab_map["求职信"]:
            render_cover_letter_tab(st.session_state.get("analytics"))


# ============================================================
# 主应用
# ============================================================
style, include_cover_letter, include_interview, selected_model = render_sidebar()
api_key = get_api_key()
client = get_openai_client(api_key) if api_key else None

st.title("CareerLens")
st.markdown(
    '<p class="app-subtitle">智能简历优化与职位匹配分析，为每一次投递提供更清晰的判断。</p>',
    unsafe_allow_html=True,
)

if st.session_state.get("show_welcome"):
    st.markdown(
        """
        <div class="welcome-card">
            <strong>欢迎使用 CareerLens。</strong>
            粘贴简历和目标 JD 后，系统会生成优化简历、匹配洞察、学习路径、面试准备和求职信。
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("关闭欢迎提示"):
        st.session_state["show_welcome"] = False
        st.rerun()

if not api_key:
    render_api_key_guide()

resume_text, jd_text, should_analyze = render_inputs()

if should_analyze:
    if not resume_text.strip() or not jd_text.strip():
        render_notice("请先填写简历和职位描述。两项内容都完整后，才能进行智能优化与分析。")
    elif client is None:
        render_notice(f"请先在 Streamlit Secrets 中配置 {API_KEY_NAME}，然后再开始分析。")
    else:
        with st.spinner("正在分析简历与职位描述，请稍候。"):
            try:
                raw_response = call_model(
                    client=client,
                    model_name=selected_model,
                    resume_text=resume_text.strip(),
                    jd_text=jd_text.strip(),
                    style=style,
                    include_cover_letter=include_cover_letter,
                    include_interview=include_interview,
                )
                tailored_resume, analytics, warning = parse_model_response(raw_response)
                st.session_state["raw_response"] = raw_response
                st.session_state["tailored_resume"] = tailored_resume
                st.session_state["analytics"] = analytics
                st.session_state["analysis_warning"] = warning
                st.rerun()
            except Exception as error:
                render_notice(explain_api_error(error))

render_results(include_cover_letter, include_interview)
