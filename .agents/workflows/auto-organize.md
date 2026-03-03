---
description: Phân loại sách mới từ Inbox bằng AI Agent
---

# /auto-organize — Phân loại sách tự động

Agent phân loại sách → di chuyển → tạo bìa (WebP) → viết mô tả → cập nhật website.

## ⚠️ CRITICAL: Quy tắc chống upload lại toàn bộ

- `generate_data.py` chỉ được chạy **ĐÚng 1 LẦN** sau khi di chuyển file.
- **PHẢI kiểm tra PyMuPDF đã cài** trước khi chạy `generate_data.py`.
- **PHẢI verify** `download_url` không bị mất sau khi `generate_data.py` chạy.
- **PHẢI chạy `--dry-run`** trước upload thật và đếm số file — nếu nhiều hơn số sách mới → DỪNG LẠI.
- **CHỈ upload sách MỚI** — nếu `--dry-run` hiện >N file (N = số sách mới) → có lỗi, KHÔNG upload.

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
   - Viết sẵn description theo **format 3 phần** (Context + Overview + Key Takeaways)
   - Hiển thị kết quả cho user xem trước
   - Đợi user xác nhận

6. Sau khi user xác nhận, di chuyển file:

```bash
mv "Inbox/[filename]" "Books/[category]/[topic]/[filename]"
```

> **LƯU Ý**: Đường dẫn đích luôn bắt đầu bằng `Books/`.

// turbo 7. **KIỂM TRA DEPENDENCIES** trước khi tạo bìa:

```bash
python -c "import fitz; print('PyMuPDF OK')" 2>&1 || echo "MISSING: cần cài PyMuPDF"
```

Nếu thiếu PyMuPDF → cài `pip install PyMuPDF` TRƯỚC khi tiếp tục. **TUYỆT ĐỐI KHÔNG** chạy `generate_data.py` khi thiếu PyMuPDF.

// turbo 8. Tạo bìa sách (WebP 250px) và cập nhật data.json — **CHỈ CHẠY 1 LẦN DUY NHẤT**:

```bash
python scripts/generate_data.py --base-dir .
```

> Script xuất trực tiếp WebP (250px, quality 60), không cần chạy optimize riêng.
> ⚠️ KHÔNG chạy lại lần 2 nếu đã chạy thành công!

// turbo 9. **VERIFY** `download_url` preservation — ĐÂY LÀ BƯỚC BẮT BUỘC:

```bash
python -c "import json; data=json.load(open('site/data.json','r',encoding='utf-8')); missing=[b['title'] for b in data if not b.get('download_url')]; print(f'Sách thiếu download_url: {len(missing)}'); [print(f'  - {t}') for t in missing]"
```

- Kết quả PHẢI chỉ hiện đúng **N cuốn sách mới** (N = số sách vừa di chuyển).
- Nếu hiện **nhiều hơn N** → `generate_data.py` đã xóa mất `download_url` cũ → **DỪNG LẠI**, báo lỗi cho user, KHÔNG upload.

10. Mở `site/data.json`, tìm entry mới (description sẽ trống ""), và cập nhật description 3 phần đã viết ở bước 5. Dùng `\n\n` ngăn cách đoạn, `•` cho bullet points.

11. **DRY-RUN upload** — BẮT BUỘC kiểm tra trước:

```bash
python scripts/upload_releases.py --dry-run
```

- Đếm số file sẽ upload.
- Nếu **đúng N file** (N = số sách mới) → OK, tiếp tục.
- Nếu **nhiều hơn N** → có lỗi preserve `download_url` → **DỪNG LẠI**, báo lỗi.

12. Upload sách mới lên GitHub Releases (chỉ khi dry-run OK):

```bash
python scripts/upload_releases.py
```

> Script tự diff local vs data.json, chỉ upload file MỚI.

13. Báo cáo kết quả cho user:
    - File đã chuyển đến đâu (trong `Books/`)
    - Bìa đã tạo (WebP) chưa
    - Description đã cập nhật chưa (format 3 phần)
    - data.json đã cập nhật chưa
    - Số file thực sự upload (phải = N sách mới)
    - Link detail view: `?book={id}`
