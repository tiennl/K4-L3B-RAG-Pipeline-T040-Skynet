# RAG evaluation results

## Run information

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-26 (UTC) |
| Framework and version | RAGAS 0.4.3 |
| Evaluator model | `gpt-4o-mini` (temperature 0) |
| Generator model | `gpt-4o-mini` (temperature 0.3) |
| Embedding model | `text-embedding-3-small` |
| Corpus version/commit | `364e314` |
| Golden dataset size | 15 questions: 13 in-domain, 2 safe-refusal cases |
| `top_k` | 5 |
| Fallback threshold and calibration | `0.55`, selected from six prior calibration queries (in-domain 0.6690–0.7000; out-of-domain 0.2804–0.4242) |

The reproducible evidence is in `ab_results.json`. RAGAS ran all four metrics on every question for both configurations; the artifact contains the generated answer, retrieved chunk IDs, row score and retrieval-plus-generation latency.

## Configurations

- **Config A — dense-only:** Chroma cosine retrieval, no RRF fusion; the same `top_k=5`, context ordering, system prompt and generator were used.
- **Config B — hybrid + RRF:** dense retrieval fused with BM25 using RRF (`k=60`); all other parameters were identical to Config A.

## Overall scores

| Metric | Config A | Config B | Delta B-A |
| --- | ---: | ---: | ---: |
| Faithfulness | 0.7200 | 0.7533 | +0.0333 |
| Answer relevance | 0.3480 | 0.3921 | +0.0441 |
| Context recall | 0.7000 | 0.7667 | +0.0667 |
| Context precision | 0.7440 | 0.7783 | +0.0343 |
| **Average** | **0.6280** | **0.6726** | **+0.0446** |

## A/B comparison

- Cấu hình tốt hơn: **Config B — hybrid + RRF**.
- Evidence: Hybrid+RRF cao hơn Config A ở cả 4 metrics. Mức tăng lớn nhất là context recall (+0.0667), cho thấy BM25/RRF bổ sung được evidence bị dense-only bỏ sót.
- Trade-off về latency/cost: Trung bình retrieval + generation là 2.334 giây ở B so với 2.442 giây ở A trong lần chạy này (-0.108 giây). Hai cấu hình dùng cùng generator và evaluator, nên chi phí LLM giống nhau; B chỉ thêm BM25/RRF cục bộ.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Doanh thu 500 triệu đồng một năm có phải nộp thuế TNCN không? | B | 0.0000 | 0.0000 | 0.0000 | 1.0000 | generation/data | Bot safe-refusal dù chunk pháp lý chứa ngưỡng 500 triệu; context còn có đoạn dễ gây nhầm lẫn giữa đúng bằng và trên 500 triệu. |
| 2 | Cách nướng cá basa bằng nồi chiên không dầu? | B | 0.0000 | 0.0000 | 0.0000 | 0.0000 | evaluation / out-of-domain | Safe refusal là hành vi mong muốn, nhưng RAGAS grounded metrics so reference/refusal với context thuế không liên quan nên chấm 0. |
| 3 | Hồ sơ đăng ký thành lập hộ kinh doanh mới tại cơ quan đăng ký kinh doanh gồm những gì? | B | 0.0000 | 0.0000 | 0.0000 | 0.0000 | evaluation / out-of-domain | Câu hỏi nằm ngoài corpus thuế và chatbot đã từ chối an toàn; bộ metric hiện tại không tách riêng chất lượng từ chối an toàn. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| ---: | --- | --- | --- | --- |
| 1 | Thêm test hồi quy cho ranh giới “doanh thu đúng 500 triệu” và ưu tiên chunk Điều 4 của NĐ 68 trong context. | Case TNCN 500 triệu của B bị từ chối dù evidence có trong corpus. | Tăng faithfulness và relevance cho các câu ngưỡng thuế. | Chạy golden case này; câu trả lời phải khẳng định không phải nộp TNCN và trích đúng document. |
| 2 | Đánh giá safe refusal bằng metric/phân lớp riêng và tách 2 câu out-of-domain khỏi bảng RAG grounded. | Hai refusal đúng làm giảm cả bốn metric xuống 0 do cách chấm không phù hợp. | Báo cáo phản ánh đúng độ an toàn thay vì phạt hành vi mong muốn. | Kiểm tra exact-match `SAFE_REFUSAL`, `sources=[]` và `retrieval_source=none` cho OOD. |
| 3 | Ưu tiên legal chunks và thêm reranker theo ngữ nghĩa pháp lý sau RRF. | Một số top-5 vẫn lẫn chunk tin tức hoặc đoạn cùng chủ đề nhưng không quyết định. | Tăng precision, giảm suy luận từ evidence không đủ. | Chạy lại A/B; mục tiêu context precision của B không thấp hơn 0.80 trên 13 câu in-domain. |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | --- | --- | --- |
| Hybrid RRF thay dense-only | Dense-only | Average +0.0446; recall +0.0667 | -0.108 giây retrieval + generation trong lần chạy | Giữ hybrid+RRF làm cấu hình mặc định. |
