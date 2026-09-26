from pathlib import Path

from app import assistant_message_from_result
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).parent.parent / "app.py"


def test_assistant_message_from_result_preserves_generated_answer_and_sources():
    """Kết quả generation phải sẵn sàng để render ngay trong lịch sử hội thoại."""
    result = {
        "answer": "Câu trả lời có căn cứ.",
        "sources": [{"content": "Đoạn nguồn", "metadata": {}}],
        "retrieval_source": "hybrid",
    }

    assert assistant_message_from_result(result) == {
        "role": "assistant",
        "content": "Câu trả lời có căn cứ.",
        "sources": [{"content": "Đoạn nguồn", "metadata": {}}],
    }


def test_app_places_a_real_query_form_inside_the_hero_workspace():
    """Người dùng phải nhập và gửi câu hỏi ngay trong workspace, không ở đáy trang."""
    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert app.slider[0].label == "Số nguồn tham khảo"
    assert app.text_input[0].label == "Hãy nhập câu hỏi của bạn"
    assert any(button.label == "Gửi câu hỏi" for button in app.button)
    assert not app.chat_input


def test_compact_workspace_keeps_verified_rag_context_without_landing_sections():
    """Màn hình đầu ưu tiên tra cứu, không thêm các section landing dài."""
    app = AppTest.from_file(str(APP_PATH)).run()

    rendered_copy = " ".join(element.value for element in app.markdown)

    assert not app.exception
    assert "Không gian tra cứu có trích nguồn" in rendered_copy
    assert "Thủ tục hành chính" in rendered_copy
    assert "Nguồn chính thức" in rendered_copy
    assert "Năng lực của trợ lý" not in rendered_copy
    assert "Thông tin có căn cứ, sử dụng có trách nhiệm" not in rendered_copy


def test_suggested_question_prefills_the_hero_query_field():
    """Một prompt gợi ý phải điền thẳng vào form chat trong hero."""
    app = AppTest.from_file(str(APP_PATH)).run()

    app.button[0].click().run()

    assert app.text_input[0].value == "Hộ kinh doanh phải kê khai thuế khi nào?"


def test_suggestion_chips_disappear_after_the_conversation_starts():
    """Gợi ý chỉ phục vụ onboarding, không chiếm chỗ khi đã có hội thoại."""
    app = AppTest.from_file(str(APP_PATH)).run()
    app.session_state["messages"] = [
        {"role": "user", "content": "Câu hỏi trước đó", "sources": []}
    ]
    app.run()

    button_labels = [button.label for button in app.button]

    assert "Hộ kinh doanh phải kê khai thuế khi nào?" not in button_labels
    assert "Gửi câu hỏi" in button_labels


def test_app_uses_compact_initial_portal_layout():
    """Màn hình ban đầu ưu tiên tra cứu, không giữ khoảng trống landing page lớn."""
    app = AppTest.from_file(str(APP_PATH)).run()

    theme = app.markdown[0].value

    assert "min-height:420px" not in theme
    assert "min-height:220px" not in theme
    assert "hero-workspace" in theme


def test_hero_copy_stays_inside_navy_workspace():
    """Nội dung hero không tràn khỏi workspace navy ở desktop."""
    app = AppTest.from_file(str(APP_PATH)).run()

    theme = app.markdown[0].value

    assert "box-sizing:border-box" in theme
    assert "max-width:1180px" in theme
