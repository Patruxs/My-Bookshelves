---
name: auto-organize
description: Tự động phân loại sách mới trong Inbox vào đúng thư mục thể loại/chủ đề bằng Antigravity AI Agent
---

# Auto-Organize Skill — Batch Mode

> **Nguyên tắc:** Phân loại TẤT CẢ → hỏi user **1 lần** → di chuyển + bìa + mô tả + upload hàng loạt.

## ⚠️ Quy tắc bảo vệ dữ liệu

| Quy tắc | Chi tiết |
|---------|----------|
| `generate_data.py` CHỈ 1 LẦN | Nếu fail → fix root cause, KHÔNG chạy lại |
| Verify PyMuPDF + Pillow | PHẢI có cả 2 trước khi generate. Dùng `python -m pip install` |
| Verify `download_url` | Sau generate: số thiếu URL = đúng N sách mới. Nếu > N → DỪNG |
| **Verify `topic` sub-folder** | Sau generate: kiểm tra sách trong sub-topic (VD: `Java/`) có `topic` chứa đầy đủ path (`Programming Languages/Java`) không. Nếu thiếu → sửa ngay |
| Dry-run upload | BẮT BUỘC trước upload thật. Count > N → DỪNG |
| Mất `download_url` | Khôi phục: `git checkout site/data.json` |
| **Folder vs Display name** | Folder trên disk dùng `Snake_Case`, nhưng trường `topic`/`category` trong `data.json` dùng display name (khoảng trắng). VD: folder `Programming_Languages/Java` → topic `"Programming Languages/Java"`. KHÔNG BAO GIỜ ghi `_` vào `data.json` |

## Quy trình thực thi

### Bước 1–3: Chuẩn bị

1. Đọc `prompts/classify_book.md` để nắm quy tắc phân loại.
2. Quét `Inbox/`, ghi nhận **N = tổng số sách mới** (.pdf/.epub). Nếu rỗng → dừng.
3. Chuẩn hóa tên: `python scripts/cli.py rename --base-dir .` → nếu cần → `--execute`.

### Bước 4: Context Grounding (BẮT BUỘC)

```bash
python scripts/cli.py structure --base-dir .
```

Sau đó dùng `view_file` đọc toàn bộ `library_structure.log`. Chú ý phần **AVAILABLE CATEGORIES** ở cuối — đây là danh sách folder có sẵn mà Agent phải ưu tiên dùng.

### Bước 5: Batch Classify + Descriptions (trong bộ nhớ)

Với mỗi file trong Inbox, Agent xác định trong bộ nhớ:
- `category_folder` + `topic_folder` (đối chiếu với log, ưu tiên CÓ SẴN)
- `description` viết theo **O'Reilly style** — 3 đoạn prose tự nhiên, KHÔNG dùng label:
  1. **Đoạn 1** (bối cảnh): Nêu vấn đề/thách thức mà sách giải quyết
  2. **Đoạn 2** (tổng quan): Giới thiệu sách, tác giả, phương pháp tiếp cận
  3. **Đoạn 3** (bullets): 4-5 `•` bullets bắt đầu bằng động từ (Master, Build, Learn, Explore, Implement...)
  
  Ngăn cách 3 đoạn bằng `\n\n`. **CẤM** dùng label `Context:`, `Overview:`, `Key Takeaways:`.

**Ngôn ngữ description:**
- Tên file tiếng Anh → viết English
- Tên file tiếng Việt (dấu hoặc pattern VN: `Ch01_`, `Giao_trinh_`, `PTTKHT`...) → viết tiếng Việt

> ⚠️ KHÔNG hỏi user từng cuốn. Xử lý TẤT CẢ rồi mới hiển thị.

### Bước 6: Hiển thị bảng + Xác nhận

In bảng tổng hợp DUY NHẤT:

```
| # | File | Category → Topic | Mô tả (tóm tắt) |
```

Hỏi user **1 LẦN DUY NHẤT**. Nếu chỉnh sửa → sửa trong bộ nhớ → hiện lại bảng.

### Bước 7–8: Di chuyển + Dependencies

7. Di chuyển batch: `mkdir -p` + `mv` gộp ít lệnh nhất. Đích luôn bắt đầu `Books/`.
8. Kiểm tra dependencies:
```bash
python -c "import fitz; print('PyMuPDF OK')" 2>&1 || echo "MISSING"
python -c "from PIL import Image; print('Pillow OK')" 2>&1 || echo "MISSING"
```
Thiếu → `python -m pip install PyMuPDF` / `Pillow`. **KHÔNG generate khi thiếu.**

### Bước 9: Generate covers + data.json (CHỈ 1 LẦN)

```bash
python scripts/cli.py generate --base-dir .
```

### Bước 10: Verify download_url

```bash
python -c "import json; data=json.load(open('site/data.json','r',encoding='utf-8')); missing=[b['title'] for b in data if not b.get('download_url')]; print(f'Thiếu URL: {len(missing)}'); [print(f'  - {t}') for t in missing]"
```

- Thiếu == N → ✅ OK. Thiếu > N → ❌ DỪNG, `git checkout site/data.json`.

### Bước 10b: Verify `topic` cho sub-topic (BẮT BUỘC)

```bash
python -c "import json; d=json.load(open('site/data.json','r',encoding='utf-8')); errors=[(b['title'],b['topic'],b['file_path']) for b in d if b['file_path'].count('/')>=4 and '/'.join(b['file_path'].split('/')[2:-1]).replace('_',' ')!=b['topic']]; print(f'Sub-topic mismatches: {len(errors)}'); [print(f'  ❌ {t} | topic={tp} | path={p}') for t,tp,p in errors]"
```

> ⚠️ Nếu có mismatch: sửa trường `topic` trong data.json. Luôn dùng **display name** (khoảng trắng), KHÔNG dùng `Snake_Case` (`_`).
> Đúng: `"topic": "Programming Languages/Java"` ✅
> Sai: `"topic": "Programming_Languages/Java"` ❌ (sẽ tạo topic trùng lặp trên UI)

### Bước 11: Chèn descriptions hàng loạt

Dùng `multi_replace_file_content` chèn TẤT CẢ `"description": ""` cùng lúc. KHÔNG edit từng entry.

> ⚠️ **JSON newline:** Dùng `\n` (single escape) cho xuống dòng, KHÔNG dùng `\\n` (double escape).
> `"Dòng 1.\n\nDòng 2."` ✅ — `"Dòng 1.\\n\\nDòng 2."` ❌ (hiển thị literal `\n`).

### Bước 12: Cập nhật library_structure.log (BẮT BUỘC)

```bash
python scripts/cli.py structure --base-dir .
```

> Log PHẢI cập nhật ngay sau khi phân loại xong, tránh topic trùng lặp lần sau.

### Bước 13–14: Upload

13. Dry-run: `python scripts/cli.py upload --dry-run` → đếm = N → OK. > N → DỪNG.
14. Upload: `python scripts/cli.py upload` (chỉ file mới).

### Bước 15: Commit + Push

```bash
git add -A && git commit -m "add: [N] books to library" && git push
```

### Bước 16: Báo cáo

```
✅ Hoàn tất: N cuốn sách đã xử lý

| # | Sách | Đích | Bìa | Mô tả | Upload |
📤 Upload: N file mới (KHÔNG re-upload sách cũ)
🔗 Links: ?book={id1}, ?book={id2}, ...
```
