"""Giao diện Streamlit cho chatbot thuế và nghĩa vụ kê khai hộ kinh doanh."""

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

SUGGESTED_QUESTIONS = [
    "Hộ kinh doanh phải kê khai thuế khi nào?",
    "Doanh thu nào được miễn thuế GTGT và TNCN?",
    "Khi nào hộ kinh doanh phải dùng hóa đơn điện tử?",
    "Điều kiện để đăng ký hộ kinh doanh là gì?",
]

KNOWLEDGE_CATEGORIES = [
    "Thủ tục hành chính",
    "Chính sách thuế",
    "Biểu mẫu và hồ sơ",
    "Văn bản pháp lý",
    "Câu hỏi thường gặp",
]


def source_label(source: dict, index: int) -> str:
    """Tạo nhãn đầy đủ, hiển thị được cho một nguồn truy xuất."""
    metadata = source["metadata"]
    return (
        f"{index}. Tiêu đề: {metadata['title']} | Nguồn: {metadata['source']} | "
        f"Phương thức: {source['retrieval_method']} | Điểm: {source['score']:.3f}"
    )


def render_sources(sources: list[dict]) -> None:
    """Hiển thị metadata và trích đoạn nguồn để kiểm chứng câu trả lời."""
    if not sources:
        return
    st.markdown(
        '<div class="citation-header"><p class="sources-heading">Nguồn tham khảo</p>'
        '<span class="status-badge official">Nguồn chính thức</span>'
        '<span class="status-badge verified">Đã xác thực</span></div>',
        unsafe_allow_html=True,
    )
    for index, source in enumerate(sources, start=1):
        with st.expander(source_label(source, index)):
            metadata = source["metadata"]
            st.caption(
                f"Loại nguồn: {metadata['doc_type']} · Đoạn: {metadata['chunk_index']}"
            )
            if metadata.get("url"):
                st.link_button("Mở nguồn gốc", metadata["url"])
            st.markdown(source["content"])


def assistant_message_from_result(result: dict) -> dict:
    """Chuẩn hóa kết quả generation để render và lưu lịch sử trong cùng lượt submit."""
    return {
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    }


def render_conversation(slot, messages: list[dict]) -> None:
    """Thay nội dung vùng hội thoại bằng lịch sử hiện tại mà không cần rerun."""
    slot.empty()
    with slot.container():
        if not messages:
            st.markdown(
                '<div class="assistant-empty"><strong>Nguồn chính thức · Đã xác thực</strong>'
                "Tôi chỉ trả lời dựa trên tài liệu có thể kiểm chứng. Hãy đặt câu hỏi để bắt đầu tra cứu.</div>",
                unsafe_allow_html=True,
            )
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                render_sources(message.get("sources", []))


def apply_theme() -> None:
    """Áp dụng ngôn ngữ thị giác cho cổng thông tin RAG chính thức."""
    st.markdown(
        """
        <style>
        :root { --navy:#17324d; --navy-deep:#102638; --ivory:#fffdf8; --beige:#f7f2ea; --saffron:#c87932; --green:#4e6b57; --ink:#24313b; --muted:#65717a; --line:#dfd8cd; --white:#fff; }
        .stApp { background:var(--beige); color:var(--ink); font-family:Arial, sans-serif; }
        .main .block-container { background:var(--ivory); box-shadow:0 18px 42px rgba(23,50,77,.12); max-width:1180px; min-height:100vh; padding:1rem 2rem 1.5rem; }
        #MainMenu, footer, header[data-testid="stHeader"] { visibility:hidden; }
        .official-header { align-items:center; border-bottom:1px solid var(--line); display:flex; gap:.75rem; padding:.55rem .15rem .75rem; }
        .brand-row { align-items:center; display:flex; gap:.7rem; }
        .agency-mark { align-items:center; background:var(--navy); border-radius:50%; color:var(--white); display:inline-flex; font-family:Georgia, serif; font-size:.68rem; font-weight:700; height:2.35rem; justify-content:center; letter-spacing:.05em; width:2.35rem; }
        .brand-copy { line-height:1.25; } .brand-copy strong { color:var(--navy); display:block; font-family:Georgia, serif; font-size:1.05rem; } .brand-copy span { color:var(--muted); font-size:.72rem; }
        .language-control { border:1px solid var(--line); border-radius:999px; color:var(--navy); font-size:.72rem; font-weight:700; margin-left:auto; padding:.4rem .75rem; }
        .st-key-hero-workspace { background:var(--navy); border:1px solid var(--navy-deep); border-radius:12px; box-sizing:border-box; margin-top:1rem; max-width:1180px; overflow:hidden; padding:1.15rem; position:relative; }
        .st-key-hero-workspace::before { border:1px solid rgba(255,255,255,.15); border-radius:50%; content:""; height:16rem; position:absolute; right:-5rem; top:-10rem; width:16rem; }
        .hero-kicker,.section-label,.sources-heading { font-size:.72rem; font-weight:800; letter-spacing:.11em; text-transform:uppercase; }
        .hero-kicker { color:#f5cd9e; margin:0 0 .35rem; } h1.hero-heading { color:var(--white)!important; font-family:Georgia, serif; font-size:clamp(1.55rem,2.6vw,2.25rem); line-height:1.1; margin:0; } .hero-description { color:#dbe6eb; font-size:.84rem; line-height:1.5; margin:.5rem 0 .55rem; }
        .section-label { color:var(--navy); margin:.1rem 0 .45rem; }
        .st-key-hero-workspace .section-label { color:#f5cd9e; }
        .stButton > button { background:var(--white); border:1px solid var(--line); border-radius:7px; box-shadow:0 3px 9px rgba(23,50,77,.05); color:var(--navy); font-size:.78rem; font-weight:700; min-height:3.35rem; padding:.55rem .7rem; text-align:left; white-space:normal; width:100%; } .st-key-hero-workspace .stButton > button { min-height:2.6rem; }
        .stButton > button:hover,.stButton > button:focus-visible { border-color:var(--saffron); box-shadow:0 5px 14px rgba(200,121,50,.18); color:var(--saffron); }
        .st-key-knowledge-panel { background:#f3ede4; border:1px solid var(--line); border-radius:8px; padding:.8rem; } .category-panel h3 { color:var(--navy); font-family:Georgia, serif; font-size:1rem; margin:0 0 .2rem; } .category-panel p { color:var(--muted); font-size:.72rem; line-height:1.4; margin:.2rem 0; } .category-list { list-style:none; margin:.45rem 0 .65rem; padding:0; } .category-list li { border-bottom:1px solid #e3dbd0; color:var(--navy); font-size:.78rem; font-weight:700; padding:.48rem 0; }
        .st-key-chat-panel { background:var(--white); border-radius:8px; padding:.8rem; } .chat-panel-title { align-items:center; display:flex; justify-content:space-between; margin-bottom:.35rem; } .chat-panel-title h3 { color:var(--navy); font-family:Georgia, serif; margin:0; } .status-badge { border-radius:999px; display:inline-block; font-size:.64rem; font-weight:800; margin-right:.25rem; padding:.24rem .45rem; } .official { background:#f4e4d2; color:#8c531e; } .verified { background:#e3ebe4; color:#355540; } .latest { background:#e7eef3; color:#234d6d; }
        .assistant-empty { background:#f7f3ed; border-left:3px solid var(--saffron); color:var(--ink); font-size:.84rem; line-height:1.5; padding:.75rem; } .assistant-empty strong { color:var(--navy); display:block; margin-bottom:.2rem; }
        [data-testid="stChatMessage"] { background:var(--white)!important; border:1px solid var(--line); border-radius:8px; box-shadow:none; color:var(--ink)!important; margin-bottom:.85rem; padding:.85rem; } [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"], [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * { color:var(--ink)!important; }
        .citation-header { align-items:center; display:flex; gap:.3rem; margin-top:1rem; } .sources-heading { color:var(--navy); margin:0 .5rem 0 0; }
        [data-testid="stExpander"] { background:var(--ivory); border:1px solid var(--line); border-radius:7px; margin:.45rem 0; }
        .feedback-row { align-items:center; border-top:1px solid var(--line); display:flex; gap:.5rem; margin-top:.7rem; padding-top:.55rem; } .feedback-row span { color:var(--muted); font-size:.72rem; margin-right:auto; } .feedback-row .stButton > button { min-height:auto; padding:.32rem .55rem; }
        .st-key-suggestion-chips { margin:.05rem 0 .45rem; } .st-key-suggestion-chips .stButton > button { background:#f7f3ed; border-color:#e7ded2; font-size:.72rem; font-weight:600; min-height:2rem; padding:.32rem .55rem; width:auto; }
        .st-key-hero-query-form { background:#f7f3ed; border:1px solid var(--line); border-radius:8px; padding:.55rem .7rem .7rem; } .st-key-hero-query-form [data-baseweb="input"] { background:var(--white)!important; } .st-key-hero-query-form input { color:var(--navy)!important; -webkit-text-fill-color:var(--navy)!important; } .st-key-hero-query-form input::placeholder { color:var(--muted)!important; -webkit-text-fill-color:var(--muted)!important; opacity:1; } [data-testid="stFormSubmitButton"] button { background:var(--saffron)!important; color:var(--white)!important; min-height:2.5rem; text-align:center; }
        [data-testid="stTextInput"] label, [data-testid="stSelectbox"] label, [data-testid="stSlider"] label { color:var(--navy)!important; }
        @media (max-width:768px) { .main .block-container { padding-left:1rem; padding-right:1rem; } .st-key-hero-workspace { padding:.8rem; } .official-header { align-items:flex-start; flex-wrap:wrap; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_portal_header() -> None:
    """Hiển thị nhận diện gọn cho không gian tra cứu."""
    st.markdown(
        """
        <header class="official-header">
          <div class="brand-row"><span class="agency-mark" aria-hidden="true">GKA</span>
            <div class="brand-copy"><strong>Government Knowledge Assistant</strong><span>Trợ lý tri thức dành cho công dân và hộ kinh doanh</span></div>
            <span class="language-control">Tiếng Việt</span>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_category_panel() -> int:
    """Hiển thị danh mục và bộ lọc độc lập với pipeline truy xuất."""
    st.markdown('<aside class="category-panel"><h3>Danh mục tri thức</h3><p>Khoanh vùng nội dung trước khi đặt câu hỏi.</p><ul class="category-list">' + "".join(f"<li>{category}</li>" for category in KNOWLEDGE_CATEGORIES) + "</ul></aside>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Bộ lọc tra cứu</p>', unsafe_allow_html=True)
    st.selectbox("Loại tài liệu", ["Tất cả tài liệu", "Văn bản pháp lý", "Hướng dẫn", "Biểu mẫu"], key="document-type")
    st.selectbox("Thời điểm ban hành", ["Không giới hạn", "12 tháng gần đây", "Theo năm"], key="publication-date")
    return st.slider("Số nguồn tham khảo", 3, 10, 5)


def render_feature_cards() -> None:
    """Trình bày bốn năng lực chính của RAG chatbot."""
    cards = [
        ("01", "Tra cứu chính xác theo tài liệu gốc", "Đối chiếu câu trả lời với những đoạn tài liệu đã được truy xuất."),
        ("02", "Tóm tắt văn bản dài", "Làm rõ nội dung chính, giúp đọc nhanh tài liệu hành chính và chính sách."),
        ("03", "Trích dẫn nguồn rõ ràng", "Mở nguồn gốc, xem metadata và kiểm tra căn cứ của từng câu trả lời."),
        ("04", "Hỗ trợ công dân", "Diễn đạt dễ hiểu, phù hợp với nhu cầu tra cứu của hộ kinh doanh."),
    ]
    st.markdown('<section class="feature-title"><h2>Năng lực của trợ lý</h2><p>Hệ thống được thiết kế để hỗ trợ tra cứu có trách nhiệm, không thay thế văn bản gốc.</p></section>', unsafe_allow_html=True)
    columns = st.columns(4)
    for column, (number, title, description) in zip(columns, cards):
        column.markdown(f'<article class="feature-card"><span class="feature-number">{number}</span><h3>{title}</h3><p>{description}</p></article>', unsafe_allow_html=True)


def render_trust_section() -> None:
    """Hiển thị cam kết tin cậy của cổng tra cứu."""
    st.markdown(
        """
        <section class="trust-panel"><div class="trust-title"><h2>Thông tin có căn cứ, sử dụng có trách nhiệm</h2><p>RAG chatbot kết hợp AI với tài liệu được kiểm duyệt để phục vụ tra cứu minh bạch.</p></div>
          <div class="trust-items"><div><strong>Dữ liệu chính thức</strong><span>Ưu tiên tài liệu có nguồn rõ ràng.</span></div><div><strong>Dẫn nguồn minh bạch</strong><span>Hiển thị nguồn đã dùng để tạo câu trả lời.</span></div><div><strong>Bảo mật người dùng</strong><span>Không yêu cầu cung cấp thông tin nhạy cảm để tra cứu.</span></div><div><strong>AI có kiểm duyệt</strong><span>Từ chối trả lời khi thiếu bằng chứng phù hợp.</span></div></div>
        </section>
        <footer class="portal-footer" id="lien-he"><div><strong>Government Knowledge Assistant</strong><span>Trợ lý tra cứu thông tin chính thức cho công dân và hộ kinh doanh.</span></div><div><strong>Thông tin</strong><span>Chính sách bảo mật<br>Điều khoản sử dụng<br>Trợ giúp tiếp cận</span></div><div><strong>Hỗ trợ</strong><span>Liên hệ hỗ trợ<br>Hướng dẫn sử dụng<br>Bản quyền hệ thống</span></div></footer>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Thuế & Kê khai Hộ Kinh Doanh", layout="wide")
    apply_theme()
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("suggested_query", None)

    render_portal_header()
    with st.container(key="hero-workspace"):
        category_column, chat_column = st.columns([.85, 2.15], gap="medium")
        with category_column:
            with st.container(key="knowledge-panel"):
                top_k = render_category_panel()
        with chat_column:
            st.markdown('<p class="hero-kicker">Cổng tri thức có căn cứ</p><h1 class="hero-heading" style="color:#fff!important">Không gian tra cứu có trích nguồn</h1><p class="hero-description">Hỏi về thuế, thủ tục và nghĩa vụ kê khai. Mỗi câu trả lời chỉ dựa trên tài liệu có thể kiểm chứng.</p>', unsafe_allow_html=True)
            with st.container(key="chat-panel"):
                st.markdown('<div class="chat-panel-title"><h3>Trợ lý tra cứu</h3><span class="status-badge latest">Cập nhật mới nhất</span></div>', unsafe_allow_html=True)
                if not st.session_state.messages:
                    st.markdown('<p class="section-label">Câu hỏi gợi ý</p>', unsafe_allow_html=True)
                    with st.container(key="suggestion-chips", horizontal=True, wrap=True, gap="xsmall"):
                        for index, question in enumerate(SUGGESTED_QUESTIONS):
                            if st.button(question, key=f"suggestion-{index}"):
                                st.session_state.suggested_query = question
                                st.session_state["hero-query"] = question
                                st.rerun()
                with st.container(height=300, key="conversation"):
                    conversation_slot = st.empty()
                    render_conversation(conversation_slot, st.session_state.messages)
                with st.form("hero-query-form", border=False, clear_on_submit=True):
                    query = st.text_input(
                        "Hãy nhập câu hỏi của bạn",
                        key="hero-query",
                        placeholder="Ví dụ: Hộ kinh doanh phải kê khai thuế khi nào?",
                        icon=":material/search:",
                    )
                    submitted = st.form_submit_button("Gửi câu hỏi")
                feedback_label, feedback_left, feedback_right = st.columns([2.3, 1, 1])
                with feedback_label:
                    st.markdown('<div class="feedback-row"><span>Thông tin này có hữu ích không?</span></div>', unsafe_allow_html=True)
                with feedback_left:
                    st.button("Hữu ích", key="feedback-helpful")
                with feedback_right:
                    st.button("Chưa hữu ích", key="feedback-unhelpful")

    if not submitted or not query.strip():
        return
    st.session_state.suggested_query = None
    st.session_state.messages.append({"role": "user", "content": query, "sources": []})
    with st.spinner("Đang tra cứu nguồn liên quan..."):
        result = generate_with_citation(query, top_k=top_k)
    st.session_state.messages.append(assistant_message_from_result(result))
    render_conversation(conversation_slot, st.session_state.messages)


if __name__ == "__main__":
    main()
