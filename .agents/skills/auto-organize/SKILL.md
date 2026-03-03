---
name: auto-organize
description: Tự động phân loại sách mới trong Inbox vào đúng thư mục thể loại/chủ đề bằng Antigravity AI Agent
---

# 📚 Auto-Organize Skill — Phân loại sách tự động bằng AI Agent

## Mô tả

Skill này được thực thi bởi **Antigravity AI Agent** (không cần API key ngoài).
Agent sẽ: phân loại → di chuyển → tạo bìa → tối ưu ảnh → viết mô tả → cập nhật data.json.

## Cấu trúc dự án

```
My-Bookshelves/
├── Inbox/                               # Sách mới cần phân loại
├── Books/                               # Thư viện sách đã tổ chức
│   ├── 1_Computer_Science_Fundamentals/
│   ├── 2_Software_Engineering_Disciplines/
│   ├── 3_Career_and_Professional_Development/
│   ├── 4_Miscellaneous/
│   └── 5_University_Courses/
├── site/                                # Website tĩnh (HTML/CSS/JS)
│   ├── index.html
│   ├── app.js
│   ├── data.json                        # Dữ liệu sách (auto-generated)
│   └── assets/covers/                   # Ảnh bìa sách (.webp)
├── scripts/
│   ├── generate_data.py                 # Quét sách → tạo data.json + cover WebP
│   ├── upload_releases.py              # Smart Incremental Sync → GitHub Releases
│   ├── auto_organize.py                 # Helper: quét cấu trúc thư viện
│   └── optimize_covers.py              # Legacy: re-optimize covers → WebP
└── .agents/skills/auto-organize/
    ├── SKILL.md                         # File này
    ├── prompts/classify_book.md         # Quy tắc phân loại
    └── config/settings.json             # Cấu hình
```

## Quy trình thực thi (dành cho Agent)

Khi user gọi `/auto-organize` hoặc yêu cầu phân loại sách, Agent phải thực hiện **đúng** các bước sau:

---

### Bước 1: Đọc cấu hình

Đọc file `config/settings.json` để biết:

- Tên thư mục inbox (`inbox_dir`)
- Các extension được hỗ trợ (`book_extensions`)

### Bước 2: Quét Inbox

Liệt kê tất cả file trong thư mục `Inbox/`.
Chỉ xử lý file có extension `.pdf` hoặc `.epub`.

### Bước 3: Đọc cấu trúc thư viện hiện tại

Liệt kê toàn bộ thư mục cấp 1 (category) và cấp 2 (topic):

```bash
python scripts/auto_organize.py --structure
```

### Bước 4: Phân loại từng cuốn sách

Đọc file `prompts/classify_book.md` để nắm quy tắc phân loại.

Dựa vào **tên file** để phân tích:

- Ngôn ngữ (tiếng Việt → University Courses)
- Chủ đề (Java, System Design, DevOps, AWS, v.v.)
- Loại sách (textbook, interview prep, career guide, v.v.)

Xác định:

- `category_folder`: Folder cấp 1 phù hợp nhất
- `topic_folder`: Folder cấp 2 (hoặc cấp 3) phù hợp nhất
- Nếu không có folder phù hợp → đề xuất tạo mới (Snake_Case)

### Bước 5: Báo cáo cho user

Hiển thị bảng phân loại cho user xem trước:

```
📖 File: "Clean Code.pdf"
   📂 → Books/2_Software_Engineering_Disciplines/Software_Architecture_and_Design/
   💭 Reasoning: ...
   📝 Description: "A practical guide to writing clean, maintainable code..."
```

### Bước 6: Di chuyển file (sau khi user xác nhận)

```bash
mv "Inbox/filename.pdf" "Books/category/topic/filename.pdf"
```

> **LƯU Ý**: Đường dẫn đích luôn bắt đầu bằng `Books/` (không phải root).

### Bước 7: Tạo bìa sách + cập nhật data.json

Chạy `generate_data.py` để trích xuất bìa từ PDF/EPUB:

```bash
python scripts/generate_data.py
```

Script sẽ tự động:

- Trích xuất trang đầu của PDF làm ảnh bìa
- Resize xuống **250px** width + convert sang **WebP** quality 60 (<30KB/ảnh)
- Lưu vào `site/assets/covers/` dạng `.webp`
- Cập nhật `site/data.json` với entry mới

### Bước 8: Upload sách lên GitHub Releases (Smart Incremental Sync)

Chạy script upload — CHỈ file mới sẽ được upload (không re-upload tất cả):

```bash
python scripts/upload_releases.py
```

Script sẽ tự động:

- Diff local vs data.json → tìm file MỚI
- Upload CHỈ file mới lên Release cố định (`storage-v1`)
- Cập nhật `download_url` trong `data.json`

Xem trước (không upload): `python scripts/upload_releases.py --dry-run`

### Bước 9: Cập nhật mô tả sách (3-Part Professional Format)

Sau khi `generate_data.py` chạy xong, **mô tả sách sẽ trống** (description: "").

Agent PHẢI mở `site/data.json`, tìm entry của cuốn sách vừa thêm, và viết mô tả theo **format 3 phần**:

1. **Context & Problem** (đoạn 1): Bối cảnh, tầm quan trọng, thách thức
2. **Book Overview** (đoạn 2): Giới thiệu sách, tác giả, giải pháp
3. **Key Takeaways** (4-5 bullet points): Dùng ký tự `•`, ngăn cách bằng `\n`

Các đoạn ngăn cách bằng `\n\n` trong JSON string. Sách tiếng Việt → viết tiếng Việt.

Ví dụ:

```json
"description": "Context paragraph about the problem domain...\n\nBook overview and author introduction...\n\n• Key takeaway 1\n• Key takeaway 2\n• Key takeaway 3\n• Key takeaway 4\n• Key takeaway 5"
```

### Bước 10: Xác nhận hoàn tất

Báo cáo kết quả cho user:

```
✅ Hoàn tất:
   📖 "Clean Code.pdf"
   📂 Đã chuyển: Books/2_Software_Engineering_Disciplines/Software_Architecture_and_Design/
   🖼️ Bìa: site/assets/covers/Clean_Code.webp (tối ưu WebP)
   📝 Mô tả: đã cập nhật (3 phần: Context + Overview + Key Takeaways)
   🌐 Website: đã cập nhật data.json
   🔗 Detail: https://patruxs.github.io/My-Bookshelves/?book={id}
```

---

## Quy tắc quan trọng

1. **LUÔN hỏi user xác nhận** trước khi di chuyển file
2. **Đọc `prompts/classify_book.md`** trước khi phân loại
3. **Quét lại cấu trúc thư mục** mỗi lần chạy (có thể có folder mới)
4. **Ưu tiên folder có sẵn** — chỉ đề xuất tạo mới khi thực sự cần
5. **Di chuyển từng file một** — không batch move
6. **Đường dẫn sách trong `Books/`** — tất cả sách nằm trong folder `Books/`
7. **LUÔN chạy generate_data.py** sau khi di chuyển file để tạo bìa WebP + cập nhật data.json
8. **LUÔN chạy upload_releases.py** sau generate_data.py để sync sách mới lên GitHub Releases
9. **LUÔN viết description** cho sách mới — không để trống
10. **Ảnh bìa PHẢI là WebP** — không commit ảnh JPG/PNG vào repo
