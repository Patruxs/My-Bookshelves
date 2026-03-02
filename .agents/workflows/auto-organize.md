---
description: Phân loại sách mới từ Inbox_Book bằng AI Agent
---

# /auto-organize — Phân loại sách tự động

Agent trực tiếp phân loại sách trong `Inbox_Book/` và di chuyển vào đúng folder (không cần API key).

## Các bước thực hiện

1. Đọc skill instructions tại `.agents/skills/auto-organize/SKILL.md` để nắm quy trình đầy đủ.

2. Đọc quy tắc phân loại tại `.agents/skills/auto-organize/prompts/classify_book.md`.

// turbo 3. Kiểm tra thư mục `Inbox_Book/` có file nào không:

```bash
ls "Inbox_Book/"
```

Nếu không có file nào, thông báo cho user và dừng.

// turbo 4. Quét cấu trúc thư viện hiện tại:

```bash
python scripts/auto_organize.py --structure
```

5. Với **từng file** trong Inbox_Book:
   - Phân tích tên file để xác định category và topic phù hợp nhất
   - Hiển thị kết quả phân loại cho user
   - Đợi user xác nhận

6. Sau khi user xác nhận, di chuyển file:

```bash
python scripts/auto_organize.py --move "[filename]" --to "[category]/[topic]"
```

7. Sau khi hoàn tất tất cả file, chạy lại script để cập nhật `data.json`:

```bash
python scripts/generate_data.py
```
