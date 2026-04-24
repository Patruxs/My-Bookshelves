---
trigger: always_on
glob: "**"
description: Project Rules — Kim chỉ nam cho toàn bộ quá trình phát triển My Bookshelves
---

Dự án My-Bookshelves là thư viện sách cá nhân static web host trên GitHub Pages.

## 1. CORE PHILOSOPHY

- **Apple-Style UI/UX**: Tối giản, glassmorphism (`backdrop-filter: blur(20px)`), khoảng trắng rộng, bo góc 12-16px, transition mượt. Light mode mặc định.
- **Zero-Dependency**: 100% Vanilla HTML + CSS + JS (ES6+). CẤM React/Vue/Tailwind/Bootstrap/jQuery/FontAwesome. System fonts only. Icons = SVG inline hoặc emoji.
- **Storage ≤ 5MB**: PDF/EPUB lưu trên GitHub Releases (tag `storage-v1`), KHÔNG trong git. Ảnh bìa WebP 600px q85 (<80KB). Không external resources/CDN.

## 2. CẤU TRÚC DỰ ÁN

```
Books/{N}_{Category}/{Topic}/book.pdf   # Sách (gitignored, lưu trên Releases)
site/index.html                         # Single-file HTML+CSS, SPA views
site/app.js                             # All JS logic
site/data.json                          # Metadata sách (source of truth)
site/assets/covers/*.webp               # Ảnh bìa
scripts/*.py                            # Automation scripts
library_structure.log                   # AI Context Grounding (auto-generated)
```

## 3. QUY TẮC ĐẶT TÊN

| Loại | Format | Ví dụ |
|------|--------|-------|
| File sách | ASCII Snake_Case, không dấu | `Go_With_Domain.pdf`, `Kien_truc_ung_dung_web.epub` |
| Category | `{N}_Snake_Case` | `1_Computer_Science_Fundamentals` |
| Topic | `Snake_Case` | `Data_Structures_and_Algorithms` |
| Ảnh bìa | `Sanitize_Title.webp` | `Head_First_Java_2nd_Edition.webp` |
| Scripts | lowercase_underscore | `generate_data.py` |

Tên sách: CHỈ dùng `_`, KHÔNG dùng khoảng trắng/`-`/`+`/`.`. Tiếng Việt KHÔNG DẤU.

## 4. FRONTEND

- **CSS**: Variables cho theming (`--bg`, `--accent`...). Intrinsic responsive: `clamp()`, `auto-fill`, `flex-wrap`. `@media` chỉ cho sidebar/navbar breakpoints.
- **JS**: `querySelector()`, `addEventListener()`, Fetch API. Inline `onclick` chỉ cho dynamic HTML.
- **SPA**: View switching (`#home-view`/`#detail-view`), `history.pushState` → `?book=id`.
- **Pagination**: Dynamic `calculateBooksPerPage()` — bội số của số cột, recalculate on resize.
- **Cache busting**: `fetch("data.json?v=" + Date.now(), {cache:"no-store"})`.

## 5. PYTHON SCRIPTS

- PEP 8, type hints, docstrings, `pathlib.Path`, `argparse`.
- `generate_data.py` yêu cầu **PyMuPDF + Pillow** cùng interpreter. Luôn dùng `python -m pip install`.
- Ảnh bìa: PDF page 1 → zoom 3x → resize 600px → WebP q85 method=6 → convert RGB trước save.

## 6. DATA PIPELINE — ⚠️ CRITICAL

- `generate_data.py` CHỈ CHẠY 1 LẦN. PHẢI verify PyMuPDF+Pillow trước.
- PHẢI verify `download_url` preservation sau generate (thiếu URL = đúng N sách mới).
- `upload_releases.py --dry-run` BẮT BUỘC trước upload thật.
- Description format 3 phần: Context → Overview → Key Takeaways (4-5 `•` bullets). Ngăn cách `\n\n`. Sách VN viết tiếng Việt.
- Mất `download_url` → `git checkout site/data.json` khôi phục.

## 7. GIT

KHÔNG BAO GIỜ commit: `*.pdf`, `*.epub`, `*.jpg`, `*.png`, `venv/`, `node_modules/`, IDE config.
Exception: `!library_structure.log` được phép commit.

## 8. CHỈ THỊ CHO AI

1. KHÔNG code placeholder/TODO — mọi function phải hoàn chỉnh.
2. KHÔNG đề xuất thư viện ngoài — luôn Vanilla.
3. KHÔNG chỉnh data.json mà xóa description/download_url đã có.
4. PHẢI đọc `library_structure.log` trước khi phân loại sách — ưu tiên folder CÓ SẴN.
5. PHẢI chạy `generate_structure_log.py` sau khi thêm sách mới.
6. PHẢI đọc `SKILL.md` trước khi thực hiện `/auto-organize`.
7. Hỏi user xác nhận trước khi move/rename file.
8. CSS dùng Variables, JS dùng ES6+, ảnh chỉ WebP.

## SCRIPTS (CLI & TUI)

**Giao diện tương tác TUI:**
`python scripts/tui.py`

**Giao diện dòng lệnh CLI:**

| Lệnh (`python scripts/cli.py <cmd>`) | Chức năng |
|-------|-----------|
| `list` | Liệt kê tất cả sách/topic/category |
| `rename` | Xem trước rename (dry-run) |
| `rename --execute` | Chuẩn hóa tên ASCII Snake_Case |
| `generate` | Tạo cover + data.json (CHỈ 1 LẦN) |
| `structure` | Cập nhật library_structure.log |
| `upload --dry-run` | Xem trước upload (BẮT BUỘC) |
| `upload` | Upload sách MỚI |
| `upload --force` | Re-upload tất cả |
| `upload --hard-reset` | Xóa + tạo lại release |
| `delete --book "Title"` | Xem trước xóa sách (dry-run) |
| `delete --book "Title" --execute` | Xóa sách khỏi data.json + cover |
| `delete --topic "Topic" --category "Cat"` | Xem trước xóa topic |
| `delete --topic "Topic" --category "Cat" --execute` | Xóa toàn bộ topic |
| `delete --category "Cat" --execute` | Xóa toàn bộ category |
| `delete --book "Title" --execute --delete-files` | Xóa cả file vật lý |
| `update --book "Title" --set-description "Desc"` | Xem trước update description |
| `update --book "Title" --set-description "Desc" --execute` | Update description |
| `update --book "Title" --set-category "Cat" --execute` | Chuyển sách sang category khác |
| `update --book "Title" --set-topic "Topic" --execute` | Chuyển sách sang topic khác |
| `update --topic "Old" --category "Cat" --rename "New" --execute` | Đổi tên topic |
| `update --category "Old" --rename "New" --execute` | Đổi tên category |

REPO: `Patruxs/My-Bookshelves` · branch: `main` · deploy: GitHub Pages từ `site/`
