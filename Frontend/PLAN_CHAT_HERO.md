# Kế hoạch triển khai Hero Chat Workspace

> **Dành cho tác nhân triển khai:** Thực hiện theo TDD: mỗi thay đổi hành vi phải có kiểm thử thất bại trước, rồi mới sửa mã nguồn.

**Mục tiêu:** Gói toàn bộ luồng hỏi đáp RAG vào một hero workspace ngắn, có ô nhập thật và phần trích nguồn cùng màn hình.

**Kiến trúc:** `app.py` vẫn gọi `generate_with_citation(query, top_k)` và lưu lịch sử trong `st.session_state`. Lớp giao diện thay bố cục landing dài bằng một workspace gồm thanh điều hướng gọn, bộ lọc bên trái và hội thoại/citation/form nhập bên phải. Form dùng widget Streamlit thật, không dùng HTML mô phỏng ô nhập.

**Công nghệ:** Python, Streamlit, `streamlit.testing.v1.AppTest`, pipeline RAG hiện có.

## Ràng buộc chung

- Toàn bộ copy hiển thị bằng tiếng Việt.
- Giữ nhánh `linh`; không sửa hay đưa `data/bm25_corpus.json` vào commit giao diện.
- Không dùng `st.chat_input` cố định ở đáy trang.
- Không dùng `use_container_width`; dùng widget native Streamlit trong form.
- Giữ `top_k` từ thanh trượt và giữ contract `generate_with_citation(query, top_k)`.

---

### Task 1: Đặt contract kiểm thử cho workspace hero ngắn

**Files:**
- Modify: `tests/test_app.py`
- Modify: `app.py`

**Consumes:** `AppTest.from_file()` khởi tạo ứng dụng Streamlit.

**Produces:** Contract UI: một trường nhập thật trong hero, nút gửi, thanh trượt nguồn, gợi ý và không có `chat_input` cố định.

- [ ] **Bước 1: Viết kiểm thử thất bại**

```python
def test_app_places_a_real_query_form_inside_the_hero_workspace():
    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert app.text_input[0].label == "Hãy nhập câu hỏi của bạn"
    assert app.button[-1].label == "Gửi câu hỏi"
    assert app.slider[0].label == "Số nguồn tham khảo"
    assert not app.chat_input
```

- [ ] **Bước 2: Chạy test để xác nhận đỏ**

Run: `.venv/bin/pytest tests/test_app.py::test_app_places_a_real_query_form_inside_the_hero_workspace -q`

Expected: FAIL vì app hiện chỉ có `st.chat_input` ở đáy trang.

- [ ] **Bước 3: Thay bố cục ứng dụng tối thiểu**

Tạo form bằng `st.form("hero-query-form")`, với `st.text_input("Hãy nhập câu hỏi của bạn")` và `st.form_submit_button("Gửi câu hỏi")`. Đặt form trong cột chat của hero workspace; dùng giá trị gợi ý trong `st.session_state` làm giá trị mặc định và chỉ chạy generation sau khi người dùng bấm gửi hoặc bấm gợi ý.

- [ ] **Bước 4: Chạy lại test để xác nhận xanh**

Run: `.venv/bin/pytest tests/test_app.py::test_app_places_a_real_query_form_inside_the_hero_workspace -q`

Expected: PASS.

### Task 2: Thu gọn giao diện và bảo toàn hội thoại/citation

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app.py`

**Consumes:** `render_sources(sources)`, `st.session_state.messages`, `generate_with_citation(query, top_k)`.

**Produces:** Một section hero duy nhất chứa danh mục, bộ lọc, lịch sử chat, nguồn và feedback; loại bỏ feature/trust/footer landing dài.

- [ ] **Bước 1: Viết kiểm thử thất bại**

```python
def test_compact_workspace_keeps_verified_rag_context_without_landing_sections():
    app = AppTest.from_file(str(APP_PATH)).run()
    rendered_copy = " ".join(element.value for element in app.markdown)

    assert "Không gian tra cứu có trích nguồn" in rendered_copy
    assert "Nguồn chính thức" in rendered_copy
    assert "Năng lực của trợ lý" not in rendered_copy
    assert "Thông tin có căn cứ, sử dụng có trách nhiệm" not in rendered_copy
```

- [ ] **Bước 2: Chạy test để xác nhận đỏ**

Run: `.venv/bin/pytest tests/test_app.py::test_compact_workspace_keeps_verified_rag_context_without_landing_sections -q`

Expected: FAIL vì landing sections còn được render.

- [ ] **Bước 3: Sửa CSS và render flow tối thiểu**

Giảm chiều cao hero, chuyển tiêu đề và chat panel vào `.hero-workspace`, giới hạn danh sách message bằng container có chiều cao, và bỏ lời gọi `render_feature_cards()`/`render_trust_section()`. Giữ badges, expander nguồn và feedback bên trong chat panel.

- [ ] **Bước 4: Chạy lại test để xác nhận xanh**

Run: `.venv/bin/pytest tests/test_app.py::test_compact_workspace_keeps_verified_rag_context_without_landing_sections -q`

Expected: PASS.

### Task 3: Kiểm thử luồng nhập liệu và nghiệm thu trực quan

**Files:**
- Modify: `tests/test_app.py`
- Verify: `app.py`

**Consumes:** Form query ở Task 1, `st.session_state`.

**Produces:** Regression test chứng minh người dùng có thể chọn gợi ý rồi thấy nó trong ô nhập; kiểm thử browser chứng minh form nằm trong hero.

- [ ] **Bước 1: Viết kiểm thử thất bại**

```python
def test_suggested_question_prefills_the_hero_query_field():
    app = AppTest.from_file(str(APP_PATH)).run()
    app.button[0].click().run()

    assert app.text_input[0].value == "Hộ kinh doanh phải kê khai thuế khi nào?"
```

- [ ] **Bước 2: Chạy test để xác nhận đỏ**

Run: `.venv/bin/pytest tests/test_app.py::test_suggested_question_prefills_the_hero_query_field -q`

Expected: FAIL nếu state gợi ý không được đồng bộ với form.

- [ ] **Bước 3: Hoàn thiện state gợi ý**

Khi bấm gợi ý, ghi `suggested_query`; dùng giá trị này làm `value` cho `st.text_input`; sau submit/generation, đặt lại `suggested_query` về `None` và cập nhật lịch sử message.

- [ ] **Bước 4: Chạy test đơn lẻ và toàn bộ test UI**

Run: `.venv/bin/pytest tests/test_app.py -q`

Expected: PASS, không exception.

- [ ] **Bước 5: Nghiệm thu browser**

Run: `.venv/bin/streamlit run app.py --server.headless true`

Mở `http://localhost:8501`, kiểm tra ô nhập và nút Gửi xuất hiện trong khung navy hero; đặt câu hỏi thuộc domain và xác nhận trả lời có nguồn.

- [ ] **Bước 6: Commit tách biệt giao diện**

```bash
git add app.py tests/test_app.py Frontend/PLAN_CHAT_HERO.md
git commit -m "feat(ui): consolidate rag chat into hero workspace"
```

## Tự rà soát

- Một hero workspace duy nhất: Task 2.
- Ô nhập thật và gửi được: Task 1, Task 3.
- Giữ bộ lọc/top-k, lịch sử, citation và feedback: Task 1–2.
- Không render landing dài: Task 2.
- Không đổi pipeline RAG hoặc cache BM25: ràng buộc chung.
