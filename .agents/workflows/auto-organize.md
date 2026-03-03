---
description: Phân loại sách mới từ Inbox bằng AI Agent (Batch Processing)
---

# /auto-organize — Phân loại sách tự động (Batch Mode)

Agent phân loại **TẤT CẢ** sách trong Inbox cùng lúc → hỏi user **1 lần duy nhất** → di chuyển + tạo bìa + viết mô tả + upload hàng loạt.

## ⚠️ CRITICAL: Quy tắc chống upload lại toàn bộ

- **Chuẩn hóa tên file** bằng `rename_books.py` TRƯỚC khi generate (tránh lỗi Unicode URL).
- `generate_data.py` chỉ được chạy **ĐÚNG 1 LẦN** sau khi di chuyển file.
- **PHẢI kiểm tra PyMuPDF VÀ Pillow đã cài** trước khi chạy `generate_data.py`.
- **PHẢI verify** `download_url` không bị mất sau khi `generate_data.py` chạy.
- **PHẢI chạy `--dry-run`** trước upload thật và đếm số file — nếu nhiều hơn số sách mới → DỪNG LẠI.
- **CHỈ upload sách MỚI** — nếu `--dry-run` hiện >N file (N = số sách mới) → có lỗi, KHÔNG upload.

## Dynamic Categories

- Hệ thống hỗ trợ **KHÔNG GIỚI HẠN** số lượng danh mục.
- AI được phép **tự tạo Category mới** nếu sách không phù hợp Category có sẵn.
- Category mới dùng format `{N}_Snake_Case` (số tiếp theo).
- Frontend tự động gán icon + màu badge qua hash — không cần sửa code.

## ⚡ BATCH PROCESSING — Các bước thực hiện

> **Nguyên tắc cốt lõi:** Agent suy luận hàng loạt trong bộ nhớ, chỉ hỏi user 1 lần duy nhất, và thực thi tất cả lệnh bash liên tiếp.

1. Đọc skill instructions tại `.agents/skills/auto-organize/SKILL.md` để nắm quy trình đầy đủ.

2. Đọc quy tắc phân loại tại `.agents/skills/auto-organize/prompts/classify_book.md`.

// turbo 3. Quét toàn bộ `Inbox/` để lấy danh sách N sách mới:

```bash
ls "Inbox/"
```

Nếu không có file nào, thông báo cho user và dừng.
Ghi nhận **N = tổng số file sách** (.pdf/.epub) để dùng cho verify sau.

// turbo 4. Chuẩn hóa tên file trong Inbox (ASCII Snake_Case):

```bash
python scripts/rename_books.py --base-dir .
```

Nếu dry-run hiện file cần đổi tên → chạy `--execute`:

```bash
python scripts/rename_books.py --base-dir . --execute
```

// turbo 5. Quét cấu trúc thư viện hiện tại:

```bash
python scripts/auto_organize.py --structure --base-dir .
```

6. **🧠 BATCH CLASSIFY + WRITE DESCRIPTIONS (trong bộ nhớ)**

   **Agent PHẢI xử lý TẤT CẢ N cuốn sách cùng lúc trong một lần suy luận:**

   Với mỗi file trong Inbox:
   - Phân tích tên file để xác định category và topic (dùng folder có sẵn hoặc tạo mới)
   - Soạn sẵn description theo **format 3 phần** (Context + Overview + Key Takeaways)
   - Lưu kết quả vào bộ nhớ (KHÔNG hỏi user từng file)

   > ⚠️ **KHÔNG được hỏi user xác nhận từng cuốn.** Phải xử lý hết rồi mới hiển thị.

7. **📋 IN BẢNG TỔNG HỢP DUY NHẤT** cho user xem trước toàn bộ kết quả:

   ```
   ## 📚 Kết quả phân loại (N cuốn sách)

   | # | File | Category → Topic | Mô tả (tóm tắt) |
   |---|------|-------------------|-------------------|
   | 1 | Clean_Code.pdf | Software Engineering / Software Architecture | A practical guide... |
   | 2 | Head_First_Java.pdf | Computer Science / Programming Languages/Java | Introduction to Java... |
   | ... | ... | ... | ... |

   > Bạn có muốn tiến hành di chuyển và xử lý tất cả? (Yes/No)
   ```

8. **✅ HỎI USER XÁC NHẬN ĐÚNG 1 LẦN** — Đợi user trả lời Yes/No.
   - Nếu user muốn chỉnh sửa → sửa trong bộ nhớ rồi hiện lại bảng.
   - Nếu user đồng ý → tiến hành các bước tiếp theo liên tục.

9. **Di chuyển TẤT CẢ file cùng lúc** bằng batch bash commands:

```bash
mkdir -p "Books/[category1]/[topic1]" "Books/[category2]/[topic2]" ...
mv "Inbox/[file1]" "Books/[category1]/[topic1]/[file1]"
mv "Inbox/[file2]" "Books/[category2]/[topic2]/[file2]"
# ... tất cả N file
```

> **LƯU Ý**: Đường dẫn đích luôn bắt đầu bằng `Books/`.

// turbo 10. **KIỂM TRA DEPENDENCIES** trước khi tạo bìa:

```bash
python -c "import fitz; print('PyMuPDF OK')" 2>&1 || echo "MISSING: cần cài PyMuPDF"
python -c "from PIL import Image; print('Pillow OK')" 2>&1 || echo "MISSING: cần cài Pillow"
```

Nếu thiếu PyMuPDF → cài `python -m pip install PyMuPDF`
Nếu thiếu Pillow → cài `python -m pip install Pillow`

⚠️ **LUÔN dùng `python -m pip install`** — hệ thống có thể có nhiều Python versions. **TUYỆT ĐỐI KHÔNG** chạy `generate_data.py` khi thiếu PyMuPDF hoặc Pillow.

// turbo 11. Tạo bìa sách (WebP 400px) và cập nhật data.json — **CHỈ CHẠY 1 LẦN DUY NHẤT**:

```bash
python scripts/generate_data.py --base-dir .
```

> Script xuất trực tiếp WebP (400px, quality 80), không cần chạy optimize riêng.
> ⚠️ KHÔNG chạy lại lần 2 nếu đã chạy thành công!

// turbo 12. **VERIFY** `download_url` preservation — ĐÂY LÀ BƯỚC BẮT BUỘC:

```bash
python -c "import json; data=json.load(open('site/data.json','r',encoding='utf-8')); missing=[b['title'] for b in data if not b.get('download_url')]; print(f'Sách thiếu download_url: {len(missing)}'); [print(f'  - {t}') for t in missing]"
```

- Kết quả PHẢI chỉ hiện đúng **N cuốn sách mới** (N = số sách vừa di chuyển).
- Nếu hiện **nhiều hơn N** → `generate_data.py` đã xóa mất `download_url` cũ → **DỪNG LẠI**, báo lỗi cho user, KHÔNG upload.

13. **CHÈN DESCRIPTIONS HÀNG LOẠT** — Mở `site/data.json`, tìm tất cả entry mới (description trống ""), và cập nhật description 3 phần đã soạn ở bước 6 **trong một lần chỉnh sửa duy nhất**. Dùng `\n\n` ngăn cách đoạn, `•` cho bullet points.

    > ⚠️ Dùng `multi_replace_file_content` để chèn tất cả descriptions cùng lúc — KHÔNG edit từng entry riêng lẻ.

14. **DRY-RUN upload** — BẮT BUỘC kiểm tra trước:

```bash
python scripts/upload_releases.py --dry-run
```

- Đếm số file sẽ upload.
- Nếu **đúng N file** (N = số sách mới) → OK, tiếp tục.
- Nếu **nhiều hơn N** → có lỗi preserve `download_url` → **DỪNG LẠI**, báo lỗi.

15. Upload sách mới lên GitHub Releases (chỉ khi dry-run OK):

```bash
python scripts/upload_releases.py
```

> Script tự diff local vs data.json, chỉ upload file MỚI.

16. Commit và push:

```bash
git add -A && git commit -m "add: [N] books to library" && git push
```

17. **Báo cáo kết quả tổng hợp** cho user:

```
✅ Hoàn tất: N cuốn sách đã xử lý

| # | Sách | Đích | Bìa | Mô tả | Upload |
|---|------|------|------|-------|--------|
| 1 | Clean_Code.pdf | Books/.../Software_Architecture/ | ✅ WebP | ✅ 3 phần | ✅ |
| 2 | Head_First_Java.pdf | Books/.../Java/ | ✅ WebP | ✅ 3 phần | ✅ |

📤 Upload: N file mới (KHÔNG re-upload sách cũ)
🔗 Links: ?book={id1}, ?book={id2}, ...
```
