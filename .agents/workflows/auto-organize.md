---
description: Phân loại sách mới từ Inbox bằng AI Agent (Batch Processing workflow)
---

# /auto-organize — Phân loại sách tự động (Batch Mode)

> Agent phân loại TẤT CẢ sách → hỏi user **1 lần** → di chuyển + bìa + mô tả + upload. Chi tiết đầy đủ xem `SKILL.md`.

1. Đọc skill instructions tại `.agents/skills/auto-organize/SKILL.md`.

2. Đọc quy tắc phân loại tại `.agents/skills/auto-organize/prompts/classify_book.md`.

// turbo 3. Quét Inbox, ghi nhận N sách mới:

```bash
ls "Inbox/"
```

Nếu rỗng → thông báo user, dừng.

// turbo 4. Chuẩn hóa tên file (dry-run trước, `--execute` nếu cần):

```bash
python scripts/cli.py rename --base-dir .
```

// turbo 5. Generate library structure log:

```bash
python scripts/cli.py structure --base-dir .
```

6. **BẮT BUỘC:** `view_file` đọc toàn bộ `library_structure.log`. Chú ý phần `AVAILABLE CATEGORIES`.

7. **🧠 BATCH CLASSIFY + DESCRIPTIONS** — Xử lý TẤT CẢ trong bộ nhớ. Đối chiếu log, ưu tiên folder CÓ SẴN. Soạn description 3 phần. KHÔNG hỏi user từng cuốn.

8. **📋 IN BẢNG TỔNG HỢP** → Hỏi user **1 LẦN DUY NHẤT**.

9. Di chuyển TẤT CẢ file batch (`mkdir -p` + `mv`). Đích luôn bắt đầu `Books/`.

// turbo 10. Kiểm tra dependencies:

```bash
python -c "import fitz; print('PyMuPDF OK')" 2>&1 || echo "MISSING"
python -c "from PIL import Image; print('Pillow OK')" 2>&1 || echo "MISSING"
```

// turbo 11. Generate covers + data.json — **CHỈ 1 LẦN**:

```bash
python scripts/cli.py generate --base-dir .
```

// turbo 12. Verify `download_url` (thiếu = đúng N → OK, > N → DỪNG):

```bash
python -c "import json; data=json.load(open('site/data.json','r',encoding='utf-8')); missing=[b['title'] for b in data if not b.get('download_url')]; print(f'Thiếu URL: {len(missing)}'); [print(f'  - {t}') for t in missing]"
```

13. **CHÈN DESCRIPTIONS** — `multi_replace_file_content` chèn tất cả `"description": ""` cùng lúc.

// turbo 14. Cập nhật log ngay sau phân loại:

```bash
python scripts/cli.py structure --base-dir .
```

15. **DRY-RUN upload** (count = N → OK, > N → DỪNG):

```bash
python scripts/cli.py upload --dry-run
```

16. Upload sách mới:

```bash
python scripts/cli.py upload
```

17. Commit + push:

```bash
git add -A && git commit -m "add: [N] books to library" && git push
```

18. **Báo cáo kết quả** cho user (bảng tổng kết + links).
