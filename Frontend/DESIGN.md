# Thiết kế Track D: Sinh câu trả lời và giao diện

**Ngày:** 2026-09-25

## Mục tiêu

Hoàn thiện phần Track D cho chatbot RAG về thuế và nghĩa vụ kê khai của hộ kinh doanh: sinh câu trả lời có căn cứ, giao diện Streamlit ổn định và phong cách trực quan lấy cảm hứng từ Ant Design cùng ảnh tham chiếu portal dịch vụ công.

## Phạm vi

Thiết kế này bao gồm D0 đến D3:

- `src/task10_generation.py`: sắp xếp context, định dạng context, gọi nhà cung cấp và sinh câu trả lời có citation.
- `tests/test_edge_cases.py`: kiểm thử generation với retrieval và nhà cung cấp được mô phỏng.
- `app.py`: giao diện Streamlit và phần hiển thị nguồn.

Golden dataset, đánh giá Ragas và báo cáo đánh giá thuộc các bước D4–D5. Track C vẫn sở hữu retrieval.

## Hợp đồng tích hợp

`generate_with_citation(query, top_k)` gọi hàm public `retrieve` của Track C nhưng không đọc chi tiết dense, BM25, RRF hoặc PageIndex.

Mỗi kết quả truy xuất phải theo `SearchResult`: có ID, nội dung, điểm số, metadata nguồn và phương thức `hybrid` hoặc `pageindex`. Generator trả `GenerationResult` gồm câu trả lời, các chunk gốc trong `sources` và nguồn truy xuất.

Nếu retrieval không có chunk, retrieval bị lỗi, nhà cung cấp bị lỗi hoặc trả text rỗng, generation phải trả đúng:

```text
Tôi không thể xác minh thông tin này từ nguồn hiện có.
```

với `sources=[]` và `retrieval_source="none"`.

## Thiết kế generation

`reorder_for_llm` trả về list mới, giữ nguyên toàn bộ ID và đưa các chunk xen kẽ về đầu, phần còn lại theo thứ tự đảo ngược để giảm nguy cơ bỏ sót thông tin ở giữa context.

`format_context` gắn nhãn ổn định, có thể nhìn thấy cho từng chunk:

```text
[Document N | Title: ... | Source: ...]
```

Các khóa tiếng Anh trong nhãn được giữ nguyên vì thuộc contract của pipeline. Prompt yêu cầu nhà cung cấp chỉ dùng context này và trích dẫn bằng nhãn tài liệu. Provider được chọn qua `.env`: OpenAI, Gemini hoặc Anthropic; timeout 30 giây, nhiệt độ 0.3.

## Thiết kế giao diện: Government Knowledge Assistant

Ứng dụng vẫn là Streamlit; đây là cổng thông tin RAG về thuế và nghĩa vụ kê khai của hộ kinh doanh, không phải chatbot trả lời tự do. Giao diện chuyển sang phong cách cổng thông tin chính phủ hiện đại: trang trọng, thoáng, có cấu trúc rõ ràng và làm nổi bật căn cứ nguồn của câu trả lời.

### Hệ thống thị giác

- Nền: trắng ngà và be ấm (`#F7F2EA`, `#FFFDF8`) để tạo cảm giác chính thống, dễ đọc.
- Màu chủ đạo: navy đậm (`#17324D`) cho header, footer, tiêu đề quan trọng và các khu vực cần tạo niềm tin.
- Màu nhấn: saffron/cam đất (`#C87932`) chỉ dùng cho CTA, trạng thái đang chọn và điểm nhận diện; xanh lá trầm (`#4E6B57`) dùng hạn chế cho badge xác thực.
- Typography: serif trang trọng cho tiêu đề chính; sans-serif rõ ràng cho nội dung, nhãn và metadata. Kích thước thân bài tối thiểu 16px, tương phản chữ/nền tối thiểu 4.5:1.
- Bề mặt: card trắng, viền be nhạt, bo góc 8–12px, bóng đổ rất nhẹ. Không dùng neon, gradient công nghệ hoặc chuyển động liên tục.

### Cấu trúc trang

1. Header gồm logo/dấu hiệu cơ quan, tên hệ thống, menu `Trang chủ`, `Dịch vụ`, `Văn bản`, `Hướng dẫn`, `Liên hệ`; điều khiển đổi ngôn ngữ và nút truy cập hệ thống.
2. Hero navy–be trang trọng có tiêu đề **Trợ lý Tra cứu Thông tin Chính thức**, mô tả chỉ trả lời từ tài liệu đã xác thực, ô hỏi lớn và bốn câu hỏi gợi ý.
3. Khu vực chatbot hai cột trên desktop: cột trái là danh mục tri thức và filter; cột phải là lịch sử chat, câu trả lời, trạng thái truy xuất và citation accordion. Trên mobile, cột trái chuyển lên trên chat.
4. Mỗi câu trả lời của trợ lý gồm nội dung chính, badge `Nguồn chính thức`, `Đã xác thực` và `Cập nhật mới nhất` khi có dữ liệu phù hợp; bên dưới là nguồn tham khảo có thể mở rộng, với CTA `Xem nguồn`, `Tải tài liệu` hoặc `Xem văn bản gốc` nếu metadata cung cấp URL.
5. Bên dưới chat có bốn card tính năng: tra cứu theo tài liệu gốc, tóm tắt văn bản dài, trích dẫn nguồn rõ ràng và hỗ trợ công dân/đa ngôn ngữ.
6. Khối tin cậy nêu rõ dữ liệu nguồn chính thức, trích dẫn minh bạch, bảo mật thông tin và AI kết hợp tài liệu đã kiểm duyệt. Footer navy chứa thông tin cơ quan, chính sách bảo mật, điều khoản và liên hệ hỗ trợ.

### Trạng thái và hành vi

- Câu hỏi gợi ý điền trực tiếp vào luồng hỏi đáp hiện có.
- Khi đang truy xuất, giao diện hiển thị trạng thái chờ với văn bản rõ ràng, không dùng chỉ báo mơ hồ.
- Citation chỉ được hiển thị từ `GenerationResult.sources`; không hiển thị URL do model tự sinh.
- Nếu không có bằng chứng, giữ nguyên safe refusal và không hiển thị badge xác thực hoặc nguồn rỗng.
- Nút feedback `Hữu ích`/`Chưa hữu ích` là giao diện sẵn sàng tích hợp, chưa lưu dữ liệu khi chưa có yêu cầu backend.

Ảnh tham chiếu được dùng để lấy cảm hứng về nhịp điệu portal, khoảng trắng và cấu trúc hero/card; không sao chép nhận diện, logo hoặc hình ảnh của cơ quan khác.

## Xử lý lỗi và khả năng tiếp cận

Ứng dụng hiển thị safe refusal do generation trả về mà không lộ stack trace của provider. Câu hỏi và câu từ chối được lưu trong lịch sử. Source expander dùng nhãn văn bản rõ ràng; phương thức retrieval và điểm số không chỉ được phân biệt bằng màu. Header, menu, filter, accordion và feedback có nhãn rõ ràng, focus ring nhìn thấy được và không phụ thuộc riêng vào màu để truyền đạt trạng thái.

## Kiểm chứng

- Unit test và contract test kiểm tra thứ tự chunk, nhãn context, safe refusal và public signature.
- Sau khi Track C sẵn sàng, chạy Streamlit với một câu hỏi đúng phạm vi và một câu hỏi ngoài phạm vi.
- Kiểm tra browser tại 375px, 768px, 1024px và desktop; kiểm tra metadata nguồn, responsive layout, lỗi console và cây accessibility.
- Kiểm tra một câu trả lời có nguồn, một safe refusal và trạng thái mở/đóng citation accordion.
