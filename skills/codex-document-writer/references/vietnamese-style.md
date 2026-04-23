# Vietnamese Document Style

Vietnamese documents should sound natural, specific, and professional. The reader should not need to translate vague AI wording into a real action.

## Preferred Labels

| Purpose | Label |
| --- | --- |
| chosen direction | `Quyết định` |
| current status | `Hiện trạng` |
| proof or verification | `Bằng chứng` |
| impact | `Tác động` |
| risk | `Rủi ro` |
| limitation | `Giới hạn` |
| next action | `Bước tiếp theo` |
| owner | `Người phụ trách` |

## Sentence Pattern

Use this shape for Vietnamese reports:

```text
<Chủ thể> <hành động> <đối tượng> để <kết quả hoặc lý do>.
```

Examples:

- `Nhóm phát hành cần chạy python skills/tests/smoke_test.py trước khi cập nhật changelog để số liệu phát hành dựa trên kết quả kiểm chứng mới nhất.`
- `Báo cáo nên đặt phần khuyến nghị trước bối cảnh kỹ thuật vì người duyệt cần quyết định ngân sách trước khi đọc chi tiết triển khai.`

## Filler To Remove

Avoid these when they do not add evidence:

- `nhìn chung`
- `về cơ bản`
- `có thể thấy rằng`
- `nâng cao chất lượng`
- `đảm bảo tính ổn định`
- `giải pháp toàn diện`
- `tối ưu quy trình`
- `mang lại hiệu quả cao`

## Better Rewrites

| Weak Vietnamese | Better Vietnamese |
| --- | --- |
| `Cần tối ưu quy trình để nâng cao chất lượng.` | `Nhóm cần bỏ bước nhập liệu lặp lại trong biểu mẫu để giảm lỗi khi tạo báo cáo tuần.` |
| `Giải pháp này đảm bảo tính ổn định.` | `Giải pháp này chặn commit khi security scan trả lỗi critical, nên lỗi bảo mật không đi vào nhánh chính mà không có kiểm tra.` |
| `Nội dung cần rõ ràng hơn.` | `Nội dung cần nêu người đọc là ai, họ cần quyết định gì, và bằng chứng nào hỗ trợ quyết định đó.` |

## Context Fit

- Báo cáo quản trị: đặt `Khuyến nghị`, `Tác động`, `Rủi ro`, `Bước tiếp theo` ở đầu.
- Tài liệu kỹ thuật: đặt `Mục tiêu`, `Phạm vi`, `Luồng xử lý`, `Kiểm chứng`, `Giới hạn`.
- Hướng dẫn sử dụng: đặt `Trước khi bắt đầu`, `Các bước thực hiện`, `Cách kiểm tra`, `Lỗi thường gặp`.
- Handoff: đặt `Hiện trạng`, `File đã đổi`, `Bằng chứng`, `Rủi ro`, `Bước tiếp theo`.

## Reliability Wording

Use these phrases to stay humble and useful:

- `Đã xác minh bằng <command/source>.`
- `Chưa xác minh phần <scope> vì <reason>.`
- `Dựa trên <evidence>, khả năng cao <claim>.`
- `Giả định hiện tại là <assumption>. Nếu giả định sai, rủi ro là <impact>.`
