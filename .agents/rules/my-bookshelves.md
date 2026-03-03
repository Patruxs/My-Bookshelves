---
trigger: always_on
glob: "**"
description: Project Rules — Kim chỉ nam cho toàn bộ quá trình phát triển My Bookshelves
---

Dự án My-Bookshelves là thư viện sách cá nhân static web host trên GitHub Pages.

## 1. TÔN CHỈ DỰ ÁN (CORE PHILOSOPHY)

### Apple-Style UI/UX

- Tối giản (Minimalism): Mỗi element phải có lý do tồn tại. Loại bỏ mọi thứ thừa.
- Glassmorphism: Navbar và sidebar dùng `backdrop-filter: blur(20px)` với nền bán trong suốt.
- Khoảng trắng rộng rãi: Padding/margin lớn, không chen chúc.
- Light mode mặc định, Dark mode là tùy chọn phụ.
- Bo góc lớn (`border-radius: 12px-16px`), shadow nhẹ, transition mượt trên mọi tương tác.

### Extreme Storage Optimization

- Git repo PHẢI dưới 5MB. Hiện tại ~700KB.
- File binary lớn (PDF/EPUB) KHÔNG BAO GIỜ nằm trong git history — lưu trên GitHub Releases.
- Ảnh bìa phải nén tối đa: WebP, 250px width, quality 60, target <30KB/ảnh.
- Không tải external resources (fonts, icons, CDN) — giảm network requests về 0.

### Zero-Dependency Frontend

- KHÔNG dùng bất kỳ thư viện/framework nào: React, Vue, Angular, Tailwind, Bootstrap, jQuery, FontAwesome.
- 100% Vanilla HTML + CSS + JavaScript (ES6+).
- CSS viết inline trong `<style>` tag của `index.html` (single-file architecture).

### SPA Architecture (View Switching)

- KHÔNG dùng modal/popup. Dùng SPA view switching: `#home-view` và `#detail-view`.
- Click sách → `showDetailView(bookId)` → ẩn home-view, hiển detail-view.
- Nút "← Library" hoặc click logo → `showHomeView()` → về trang chủ.
- URL dùng `history.pushState` → `?book=id`. Lắng nghe `popstate` cho nút Back trình duyệt.
- Detail view có: bìa sách lớn (360px, sticky), tags, description (pre-wrap), download/share, và Related Books (max 5).
- Related Books: cùng topic trước → cùng category nếu thiếu → tối đa 5 cuốn.

## 2. QUY TẮC QUẢN LÝ THƯ MỤC VÀ GỌI TÊN

### Dynamic Categories

Hệ thống hỗ trợ **Dynamic Categories** — không giới hạn số lượng danh mục.

- Category folders: `{số}_Snake_Case` → VD: `1_Computer_Science_Fundamentals`
- Topic folders: `Snake_Case` → VD: `Data_Structures_and_Algorithms`
- Sub-topic (nếu cần): `Snake_Case` → VD: `Programming_Languages/Java`
- Đường dẫn đầy đủ: `Books/{category}/{topic}/filename.pdf`
- AI được phép **tự tạo Category mới** nếu sách không phù hợp Category có sẵn.
- Category mới phải dùng số tiếp theo: nếu đã có 1-5, category mới là `6_Ten_Danh_Muc`.
- Frontend (`app.js`) tự động gán icon và màu badge cho category mới qua hash — không cần cập nhật code.
- Luôn ưu tiên folder **có sẵn** trước khi tạo mới.

### Files

- HTML/JS/CSS: lowercase, không dấu → `index.html`, `app.js`
- Python scripts: lowercase + underscore → `generate_data.py`, `auto_organize.py`
- Ảnh bìa: `Sanitize_Title.webp` (thay space/ký tự đặc biệt bằng `_`, max 100 chars)
- Tên file sách: **ASCII Snake_Case** không dấu → `Go_With_Domain.pdf`, `Kien_truc_ung_dung_web.epub`
  - BẮT BUỘC tiếng Việt KHÔNG DẤU (loại bỏ diacritics: ă→a, ứ→u, đ→d, v.v.)
  - CHỈ sử dụng dấu gạch dưới `_` để phân cách từ
  - KHÔNG dùng khoảng trắng ` `, dấu gạch ngang `-`, dấu cộng `+`, hay dấu chấm `.`
  - Chạy `python scripts/rename_books.py --base-dir . --execute` để chuẩn hóa tên file
  - Ví dụ ĐÚNG: `Go_With_Domain.pdf`, `Head_First_Java_2nd_Edition.pdf`, `Kien_truc_ung_dung_web.epub`
  - Ví dụ SAI: `Go With Domain.pdf`, `go-with-domain.pdf`, `Kiến trúc ứng dụng web.pdf`

### Cấu trúc thư mục chuẩn

```
Books/{1-5}_{Category}/{Topic}/book.pdf
site/index.html          # Single-file HTML+CSS, SPA views (home + detail)
site/app.js              # All JS logic: routing, rendering, detail view, related books
site/data.json           # Mảng JSON chứa metadata của tất cả sách
site/assets/covers/      # Ảnh bìa WebP (250px, q60)
scripts/*.py
.agents/skills/auto-organize/
.agents/workflows/
.agents/rules/
```

## 3. QUY TẮC FRONTEND (HTML / CSS / VANILLA JS)

### CSS

- KHÔNG Tailwind, KHÔNG Bootstrap, KHÔNG CSS framework.
- Dùng CSS Variables cho theming: `--bg`, `--text-primary`, `--accent`, `--glass`, `--radius-sm`.
- System fonts ONLY: `font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
- Responsive: 3 breakpoints — mobile (≤640px), tablet (641–1199px), desktop (≥1200px).
- Animation: chỉ CSS `transition` và `@keyframes`, KHÔNG JS animation libraries.

### Icons

- CẤM import icon fonts (FontAwesome, Material Icons, Heroicons CDN).
- BẮT BUỘC dùng SVG inline hoặc emoji.
- VD chuẩn: `<svg viewBox="0 0 24 24" width="16" height="16"><path d="..."/></svg>`

### JavaScript

- CẤM React, Vue, jQuery, Lodash, hoặc bất kỳ library nào.
- Chỉ Vanilla JS với ES6+ (arrow functions, template literals, destructuring, modules).
- DOM queries: `document.querySelector()`, `document.querySelectorAll()`.
- Events: ưu tiên `addEventListener()`. Inline `onclick` chỉ dùng cho dynamic HTML (cards, pagination) và HTML elements cố định (menu-btn, theme-toggle, sidebar overlay).
- Fetch API cho HTTP requests, không XMLHttpRequest.

## 4. QUY TẮC PYTHON (AUTOMATION SCRIPTS)

### Code Standards

- Tuân thủ PEP 8.
- Type hints cho tất cả function signatures.
- Docstrings cho mọi function (style Google/NumPy).
- Xử lý lỗi: `try/except` cho mọi import optional và file I/O.
- Path handling: dùng `pathlib.Path` cho paths. `os.walk()` được phép cho directory traversal.
- CLI: dùng `argparse` cho tất cả scripts.

### Xử lý ảnh bìa

- Width tối đa: 250px (resize bằng `Image.LANCZOS`).
- Format: WebP (method=6 cho max compression).
- Quality: 60 (target <30KB/ảnh).
- Render PDF page 1 ở zoom 2x rồi downscale → sắc nét khi thu nhỏ.
- RGBA/P mode → convert sang RGB trước khi save WebP.

### Data Pipeline — ⚠️ CRITICAL RULES

- `generate_data.py` PHẢI preserve description VÀ download_url khi regenerate data.json.
- Book ID = `hashlib.md5(file_path).hexdigest()[:12]`.
- Output cover: `site/assets/covers/{sanitize_filename(title)}.webp`.
- Graceful fallback: script vẫn chạy nếu thiếu PyMuPDF hoặc ebooklib.

**Quy tắc chống mất dữ liệu:**

- **PHẢI kiểm tra PyMuPDF đã cài** trước khi chạy `generate_data.py` (chạy thiếu PyMuPDF = risk mất data).
- **Chạy `generate_data.py` CHỈ 1 LẦN** — không chạy lặp lại. Nếu fail → fix root cause trước.
- **PHẢI verify `download_url`** ngay sau generate: đếm số sách thiếu URL phải = đúng N sách mới.
- **PHẢI chạy `upload_releases.py --dry-run`** trước upload thật: nếu dry-run hiện >N file → DỪNG.
- Nếu phát hiện mất `download_url` → `git checkout site/data.json` để khôi phục, rồi fix lại.

### Description Format (3-Part Professional)

Mọi description trong data.json PHẢI tuân thủ 3 phần:

1. **Context & Problem:** Bối cảnh, tầm quan trọng, thách thức (1 đoạn)
2. **Book Overview:** Giới thiệu sách, tác giả, giải pháp (1 đoạn)
3. **Key Takeaways:** 4-5 bullet points bằng ký tự `•` (không dùng `-`)

Các đoạn ngăn cách bằng `\n\n` trong JSON string. Sách tiếng Việt viết bằng tiếng Việt.
CSS `.dv-desc` đã có `white-space: pre-wrap` để render đúng format.

Ví dụ:

```json
"description": "Context paragraph...\n\nOverview paragraph...\n\n• Takeaway 1\n• Takeaway 2\n• Takeaway 3\n• Takeaway 4"
```

### AI Skill Prompts

- Prompts phân loại sách nằm tại `.agents/skills/auto-organize/prompts/classify_book.md`.
- Output format: JSON với fields `category_folder`, `topic_folder`, `confidence`, `reasoning`, `is_new_category`.
- Ưu tiên folder có sẵn, chỉ đề xuất tạo mới khi confidence < 0.5.

## 5. QUY TẮC GIT & LƯU TRỮ

### .gitignore BẮT BUỘC block

```
*.pdf  *.epub  *.mobi  *.azw3  *.djvu
__pycache__/  *.py[cod]  venv/
*.log  .DS_Store  Thumbs.db
.vscode/  .idea/
```

### GitHub Releases Strategy (Smart Incremental Sync)

- Sách (PDF/EPUB) upload lên GitHub Releases bằng `scripts/upload_releases.py`.
- Release tag cố định: `storage-v1` (tích lũy, không tạo mới mỗi ngày).
- Script tự diff local vs data.json → chỉ upload file MỚI, bỏ qua file đã có `download_url`.
- Sau khi upload, script tự append metadata + cập nhật `download_url` trong `data.json`.
- Download URL priority trong app.js: `download_url` → `"../" + file_path` → `raw.githubusercontent.com`.

**⚠️ UPLOAD SAFEGUARDS:**

- BẮT BUỘC chạy `--dry-run` trước upload thật.
- Đếm số file trong dry-run. Nếu > số sách mới → CÓ LỖI, KHÔNG upload.
- Chỉ upload khi dry-run count == đúng N sách mới từ Inbox.

### KHÔNG BAO GIỜ commit

- File PDF/EPUB (dù nhỏ).
- Ảnh JPG/PNG (phải convert sang WebP trước).
- Node modules, Python venv, IDE config.

## 6. CHỈ THỊ CHO AI ASSISTANT

Khi viết code cho dự án này, AI PHẢI:

1. KHÔNG viết code placeholder/TODO — mọi function phải hoạt động hoàn chỉnh.
2. KHÔNG đề xuất cài thư viện JS/CSS ngoài — luôn viết Vanilla.
3. KHÔNG tạo file ảnh JPG/PNG — luôn xuất WebP.
4. KHÔNG chỉnh sửa data.json mà xóa mất description hoặc download_url đã có.
5. LUÔN kiểm tra `.agents/skills/auto-organize/SKILL.md` trước khi thực hiện phân loại sách.
6. LUÔN hỏi user xác nhận trước khi di chuyển (move/rename) bất kỳ file nào.
7. LUÔN giữ tổng dung lượng repo dưới 5MB khi đề xuất thêm tài nguyên.
8. Khi sửa CSS: dùng CSS Variables, không hardcode màu.
9. Khi sửa JS: giữ zero-dependency, dùng ES6+.
10. Khi tạo cover mới: chạy `python scripts/generate_data.py --base-dir .` (xuất WebP trực tiếp).
11. Khi viết description: PHẢI theo format 3 phần (Context → Overview → Key Takeaways).
12. Khi đặt tên file sách: PHẢI dùng ASCII Snake_Case không dấu, KHÔNG dùng khoảng trắng, `-`, `+`, `.`.
13. **PHẢI kiểm tra PyMuPDF** trước khi chạy `generate_data.py` — KHÔNG chạy nếu thiếu.
14. **Chạy `generate_data.py` CHỈ 1 LẦN** — không chạy lại nếu đã thành công.
15. **PHẢI verify `download_url` preservation** sau khi `generate_data.py` chạy xong.
16. **PHẢI chạy `upload_releases.py --dry-run`** trước upload thật — nếu count > N sách mới → DỪNG.

SCRIPTS REFERENCE:

- `python scripts/rename_books.py --base-dir .` → xem trước file cần đổi tên (DRY-RUN)
- `python scripts/rename_books.py --base-dir . --execute` → chuẩn hóa tên file ASCII Snake_Case
- `python scripts/generate_data.py --base-dir .` → tạo cover WebP + data.json (CHỈ CHẠY 1 LẦN)
- `python scripts/upload_releases.py --dry-run` → xem trước file cần upload (BẮT BUỘC TRƯỚC UPLOAD)
- `python scripts/upload_releases.py` → Smart Incremental Sync (chỉ upload sách MỚI)
- `python scripts/upload_releases.py --force` → re-upload tất cả (CHỈ KHI CẦN)
- `python scripts/upload_releases.py --hard-reset` → XÓA release cũ, tạo mới, upload lại TẤT CẢ
- `python scripts/auto_organize.py --structure` → xem cấu trúc thư viện
- `python scripts/optimize_covers.py` → re-optimize ảnh bìa cũ sang WebP

REPO: Patruxs/My-Bookshelves, branch: main, deploy: GitHub Pages từ site/
