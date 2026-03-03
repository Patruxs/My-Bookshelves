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
- Dark mode mặc định, Light mode là tùy chọn phụ.
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

## 2. QUY TẮC QUẢN LÝ THƯ MỤC VÀ GỌI TÊN

### Thư mục sách

- Category folders: `{số}_Snake_Case` → VD: `1_Computer_Science_Fundamentals`
- Topic folders: `Snake_Case` → VD: `Data_Structures_and_Algorithms`
- Sub-topic (nếu cần): `Snake_Case` → VD: `Programming_Languages/Java`
- Đường dẫn đầy đủ: `Books/{category}/{topic}/filename.pdf`

### Files

- HTML/JS/CSS: lowercase, không dấu → `index.html`, `app.js`
- Python scripts: lowercase + underscore → `generate_data.py`, `auto_organize.py`
- Ảnh bìa: `Sanitize_Title.webp` (thay space/ký tự đặc biệt bằng `_`, max 100 chars)
- Data: `data.json` (mảng JSON, UTF-8, indent 2)

### Cấu trúc thư mục chuẩn

```
Books/{1-5}_{Category}/{Topic}/book.pdf
site/assets/covers/Book_Title.webp
site/data.json
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

### Data Pipeline

- `generate_data.py` PHẢI preserve description khi regenerate data.json.
- Book ID = `hashlib.md5(file_path).hexdigest()[:12]`.
- Output cover: `site/assets/covers/{sanitize_filename(title)}.webp`.
- Graceful fallback: script vẫn chạy nếu thiếu PyMuPDF hoặc ebooklib.

### AI Skill Prompts

- Prompts phân loại sách nằm tại `.agents/skills/auto-organize/prompts/classify_book.md`.
- Output format: JSON với fields `category_folder`, `topic_folder`, `confidence`, `reasoning`.
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

### KHÔNG BAO GIỜ commit

- File PDF/EPUB (dù nhỏ).
- Ảnh JPG/PNG (phải convert sang WebP trước).
- Node modules, Python venv, IDE config.

## 6. CHỈ THỊ CHO AI ASSISTANT

Khi viết code cho dự án này, AI PHẢI:

1. KHÔNG viết code placeholder/TODO — mọi function phải hoạt động hoàn chỉnh.
2. KHÔNG đề xuất cài thư viện JS/CSS ngoài — luôn viết Vanilla.
3. KHÔNG tạo file ảnh JPG/PNG — luôn xuất WebP.
4. KHÔNG chỉnh sửa data.json mà xóa mất description đã có.
5. LUÔN kiểm tra `.agents/skills/auto-organize/SKILL.md` trước khi thực hiện phân loại sách.
6. LUÔN hỏi user xác nhận trước khi di chuyển (move/rename) bất kỳ file nào.
7. LUÔN giữ tổng dung lượng repo dưới 5MB khi đề xuất thêm tài nguyên.
8. Khi sửa CSS: dùng CSS Variables, không hardcode màu.
9. Khi sửa JS: giữ zero-dependency, dùng ES6+.
10. Khi tạo cover mới: chạy `python scripts/generate_data.py --base-dir .` (xuất WebP trực tiếp).

SCRIPTS REFERENCE:

- `python scripts/generate_data.py --base-dir .` → tạo cover WebP + data.json
- `python scripts/upload_releases.py` → Smart Incremental Sync (chỉ upload sách MỚI)
- `python scripts/upload_releases.py --dry-run` → xem trước file cần upload
- `python scripts/upload_releases.py --force` → re-upload tất cả
- `python scripts/auto_organize.py --structure` → xem cấu trúc thư viện
- `python scripts/optimize_covers.py` → re-optimize ảnh bìa cũ sang WebP

REPO: Patruxs/My-Bookshelves, branch: main, deploy: GitHub Pages từ site/
