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
