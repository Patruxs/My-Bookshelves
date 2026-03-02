---
description: Phân loại sách mới từ Inbox bằng AI Agent
---

# /auto-organize — Phân loại sách tự động

Agent phân loại sách → di chuyển → tạo bìa (WebP) → viết mô tả → cập nhật website.

## Các bước thực hiện

1. Đọc skill instructions tại `.agents/skills/auto-organize/SKILL.md` để nắm quy trình đầy đủ.

2. Đọc quy tắc phân loại tại `.agents/skills/auto-organize/prompts/classify_book.md`.

// turbo 3. Kiểm tra thư mục `Inbox/` có file nào không:

```bash
ls "Inbox/"
```

Nếu không có file nào, thông báo cho user và dừng.

// turbo 4. Quét cấu trúc thư viện hiện tại:

```bash
python scripts/auto_organize.py --structure --base-dir .
```

5. Với **từng file** trong Inbox:
   - Phân tích tên file để xác định category và topic
   - Viết sẵn description ngắn gọn (1-2 câu)
   - Hiển thị kết quả cho user xem trước
   - Đợi user xác nhận

6. Sau khi user xác nhận, di chuyển file:

```bash
mv "Inbox/[filename]" "Books/[category]/[topic]/[filename]"
```

> **LƯU Ý**: Đường dẫn đích luôn bắt đầu bằng `Books/`.

// turbo 7. Tạo bìa sách (WebP 250px) và cập nhật data.json:

```bash
python scripts/generate_data.py --base-dir .
```

> Script xuất trực tiếp WebP (250px, quality 60), không cần chạy optimize riêng.

8. Mở `site/data.json`, tìm entry mới (description sẽ trống ""), và cập nhật description đã viết ở bước 5.

9. (Tùy chọn) Upload sách lên GitHub Releases:

```bash
python scripts/upload_releases.py
```

10. Báo cáo kết quả cho user:
    - File đã chuyển đến đâu (trong `Books/`)
    - Bìa đã tạo (WebP) chưa
    - Description đã cập nhật chưa
    - data.json đã cập nhật chưa
