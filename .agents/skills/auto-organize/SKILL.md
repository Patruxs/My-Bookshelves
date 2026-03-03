---
name: auto-organize
description: Tự động phân loại sách mới trong Inbox vào đúng thư mục thể loại/chủ đề bằng Antigravity AI Agent
---

# 📚 Auto-Organize Skill — Phân loại sách tự động bằng AI Agent

## Mô tả

Skill này được thực thi bởi **Antigravity AI Agent** (không cần API key ngoài).
Agent sẽ: chuẩn hóa tên file → phân loại → di chuyển → tạo bìa → viết mô tả → upload → cập nhật website.

## Cấu trúc dự án

```git
My-Bookshelves/
├── Inbox/                               # Sách mới cần phân loại
├── Books/                               # Thư viện sách đã tổ chức (Dynamic Categories)
│   ├── {N}_{Category_Name}/             # Category folders (số + Snake_Case)
│   │   └── {Topic_Name}/               # Topic folders (Snake_Case)
│   │       └── Book_Name.pdf           # File sách (ASCII Snake_Case, không dấu)
├── site/                                # Website tĩnh (HTML/CSS/JS)
│   ├── index.html
│   ├── app.js                           # Dynamic category icons/colors via hash
│   ├── data.json                        # Dữ liệu sách (auto-generated)
│   └── assets/covers/                   # Ảnh bìa sách (.webp)
├── scripts/
│   ├── rename_books.py                  # Chuẩn hóa tên file → ASCII Snake_Case
│   ├── generate_data.py                 # Quét sách → tạo data.json + cover WebP
│   ├── upload_releases.py               # Smart Incremental Sync → GitHub Releases
│   ├── auto_organize.py                 # Helper: quét cấu trúc thư viện
│   └── optimize_covers.py              # Legacy: re-optimize covers → WebP
└── .agents/skills/auto-organize/
    ├── SKILL.md                         # File này
    ├── prompts/classify_book.md         # Quy tắc phân loại (Dynamic Categories)
    └── config/settings.json             # Cấu hình
```

## Dynamic Categories

Hệ thống hỗ trợ **không giới hạn số lượng danh mục**:

- AI được phép **tự tạo Category mới** nếu sách không phù hợp Category có sẵn
- Category mới dùng số tiếp theo: nếu đã có 1-5, category mới là `6_Ten_Danh_Muc`
- Frontend (`app.js`) tự động gán icon và màu badge qua hash — không cần cập nhật code
- Luôn ưu tiên folder **có sẵn** trước khi tạo mới

## Quy chuẩn đặt tên file sách

- **ASCII Snake_Case** không dấu: `Go_With_Domain.pdf`, `Kien_truc_ung_dung_web.epub`
- Tiếng Việt KHÔNG DẤU (đ→d, ă→a, ứ→u, v.v.)
- CHỈ dùng `_` phân cách, KHÔNG dùng khoảng trắng, `-`, `+`, `.`
- Chạy `python scripts/rename_books.py --base-dir . --execute` để chuẩn hóa

## ⚠️ CRITICAL: Quy tắc bảo vệ dữ liệu

### Nguyên nhân lỗi phổ biến: Upload lại toàn bộ sách

Khi `generate_data.py` chạy, nó tạo lại `data.json` từ đầu. Script có logic preserve `download_url` bằng cách match `file_path` hoặc `title` từ data.json cũ. Tuy nhiên:

1. **Chạy generate_data.py khi thiếu PyMuPDF** → bìa fail → data.json có thể bị lỗi → chạy lại lần 2 có thể mất `download_url`
2. **Đổi tên file/folder** → `file_path` cũ không match → phải rely vào `title` match (rủi ro hơn). Nếu đổi tên file, chạy `rename_books.py --execute` trước — script sẽ tự cập nhật `file_path` trong data.json.
3. **Chạy generate_data.py nhiều lần** → mỗi lần nó đọc data.json hiện tại làm base → nếu lần trước đã mất URL thì lần sau không recover được

### Quy tắc bắt buộc

1. **Chuẩn hóa tên file** trước khi generate: chạy `rename_books.py --execute` nếu cần
2. **Kiểm tra PyMuPDF** trước khi chạy `generate_data.py` — KHÔNG chạy khi thiếu
3. **Chạy `generate_data.py` CHỈ 1 LẦN** — nếu fail thì fix nguyên nhân rồi mới chạy lại
4. **Verify `download_url`** ngay sau khi `generate_data.py` chạy xong
5. **Dry-run upload** trước khi upload thật — đếm file phải = đúng số sách mới
6. Nếu verify thấy mất `download_url` nhiều hơn expected → **DỪNG**, báo user

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
Ghi nhận **N = tổng số sách mới** để dùng cho bước verify sau.

### Bước 3: Chuẩn hóa tên file (ASCII Snake_Case)

```bash
python scripts/rename_books.py --base-dir .
```

Kiểm tra dry-run. Nếu có file cần đổi tên:

```bash
python scripts/rename_books.py --base-dir . --execute
```

> Bước này đảm bảo tên file ASCII-safe trước khi upload lên GitHub Releases (tránh lỗi Unicode trong URL).

### Bước 4: Đọc cấu trúc thư viện hiện tại

```bash
python scripts/auto_organize.py --structure --base-dir .
```

### Bước 5: Phân loại từng cuốn sách

Đọc file `prompts/classify_book.md` để nắm quy tắc phân loại.

Dựa vào **tên file** để phân tích:

- Ngôn ngữ (tiếng Việt → University Courses hoặc category phù hợp)
- Chủ đề (Java, System Design, DevOps, AWS, v.v.)
- Loại sách (textbook, interview prep, career guide, v.v.)

Xác định:

- `category_folder`: Folder cấp 1 phù hợp nhất (có sẵn HOẶC tạo mới)
- `topic_folder`: Folder cấp 2 (hoặc cấp 3) phù hợp nhất
- Nếu không có folder phù hợp → **TỰ DO tạo category/topic mới** (format `{N}_Snake_Case`)

### Bước 6: Báo cáo cho user

Hiển thị bảng phân loại cho user xem trước:

```
📖 File: "Clean_Code.pdf"
   📂 → Books/2_Software_Engineering_Disciplines/Software_Architecture_and_Design/
   💭 Reasoning: ...
   📝 Description: "A practical guide to writing clean, maintainable code..."
```

### Bước 7: Di chuyển file (sau khi user xác nhận)

```bash
mv "Inbox/filename.pdf" "Books/category/topic/filename.pdf"
```

> **LƯU Ý**: Đường dẫn đích luôn bắt đầu bằng `Books/` (không phải root).

### Bước 8: ⚠️ Kiểm tra dependencies (BẮT BUỘC trước generate)

```bash
python -c "import fitz; print('PyMuPDF OK')"
```

- Nếu thiếu → cài `pip install PyMuPDF` TRƯỚC khi tiếp tục.
- **TUYỆT ĐỐI KHÔNG** chạy `generate_data.py` khi thiếu PyMuPDF — sẽ tạo data.json thiếu cover và có thể mất `download_url`.

### Bước 9: Tạo bìa sách + cập nhật data.json (CHỈ 1 LẦN)

```bash
python scripts/generate_data.py --base-dir .
```

Script sẽ tự động:

- Trích xuất trang đầu của PDF làm ảnh bìa
- Resize xuống **250px** width + convert sang **WebP** quality 60 (<30KB/ảnh)
- Lưu vào `site/assets/covers/` dạng `.webp`
- Cập nhật `site/data.json` với entry mới (preserve description + download_url cũ)

> ⚠️ **KHÔNG CHẠY LẠI LẦN 2** — nếu có lỗi, fix nguyên nhân root cause trước.

### Bước 10: ⚠️ VERIFY download_url preservation (BẮT BUỘC)

```bash
python -c "import json; data=json.load(open('site/data.json','r',encoding='utf-8')); missing=[b['title'] for b in data if not b.get('download_url')]; print(f'Sách thiếu download_url: {len(missing)}'); [print(f'  - {t}') for t in missing]"
```

**Kiểm tra kết quả:**

- ✅ Số sách thiếu `download_url` == N (đúng bằng số sách mới vừa thêm) → OK
- ❌ Số sách thiếu `download_url` > N → `generate_data.py` đã xóa mất URL cũ → **DỪNG LẠI**
  - Phải khôi phục bằng `git checkout site/data.json` rồi fix nguyên nhân
  - KHÔNG tiếp tục upload trong trường hợp này

### Bước 11: Cập nhật mô tả sách (3-Part Professional Format)

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

### Bước 12: ⚠️ DRY-RUN upload (BẮT BUỘC trước upload thật)

```bash
python scripts/upload_releases.py --dry-run
```

**Kiểm tra kết quả:**

- ✅ Số file cần upload == N (đúng bằng số sách mới) → OK, tiếp tục bước 13
- ❌ Số file cần upload > N → có lỗi preserve `download_url` → **DỪNG LẠI**
  - KHÔNG chạy upload thật
  - Báo lỗi cho user kèm danh sách file bất thường

### Bước 13: Upload sách MỚI lên GitHub Releases

Chạy script upload — CHỈ file mới sẽ được upload (không re-upload tất cả):

```bash
python scripts/upload_releases.py
```

Script sẽ tự động:

- Diff local vs data.json → tìm file MỚI (thiếu `download_url`)
- Upload CHỈ file mới lên Release cố định (`storage-v1`)
- Cập nhật `download_url` trong `data.json`

### Bước 14: Commit và Push

```bash
git add -A && git commit -m "add: [tên sách] to [category/topic]" && git push
```

### Bước 15: Xác nhận hoàn tất

Báo cáo kết quả cho user:

```
✅ Hoàn tất:
   📖 "Clean_Code.pdf"
   📂 Đã chuyển: Books/2_Software_Engineering_Disciplines/Software_Architecture_and_Design/
   🖼️ Bìa: site/assets/covers/Clean_Code.webp (tối ưu WebP)
   📝 Mô tả: đã cập nhật (3 phần: Context + Overview + Key Takeaways)
   🌐 Website: đã cập nhật data.json
   📤 Upload: N file mới (đúng N sách mới, KHÔNG re-upload sách cũ)
   🔗 Detail: https://patruxs.github.io/My-Bookshelves/?book={id}
```

---

## Quy tắc quan trọng

1. **LUÔN hỏi user xác nhận** trước khi di chuyển file
2. **Đọc `prompts/classify_book.md`** trước khi phân loại
3. **Quét lại cấu trúc thư mục** mỗi lần chạy (có thể có folder mới)
4. **Ưu tiên folder có sẵn** — chỉ đề xuất tạo mới khi thực sự cần
5. **Di chuyển từng file một** — không batch move
6. **Chuẩn hóa tên file** bằng `rename_books.py` trước khi generate/upload
7. **Đường dẫn sách trong `Books/`** — tất cả sách nằm trong folder `Books/`
8. **Kiểm tra PyMuPDF** trước khi chạy `generate_data.py` — bắt buộc
9. **Chạy `generate_data.py` CHỈ 1 LẦN** — không chạy lại nếu đã thành công
10. **VERIFY `download_url`** sau khi generate — đếm số thiếu phải = đúng N sách mới
11. **DRY-RUN bắt buộc** trước upload — đếm file phải = đúng N sách mới
12. **LUÔN viết description** cho sách mới — không để trống
13. **Ảnh bìa PHẢI là WebP** — không commit ảnh JPG/PNG vào repo
14. **Dynamic Categories** — AI tự do tạo category mới khi cần (format `{N}_Snake_Case`)
