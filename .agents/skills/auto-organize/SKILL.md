---
name: auto-organize
description: Tự động phân loại sách mới trong Inbox_Book vào đúng thư mục thể loại/chủ đề bằng Antigravity AI Agent
---

# 📚 Auto-Organize Skill — Phân loại sách tự động bằng AI Agent

## Mô tả

Skill này được thực thi bởi **Antigravity AI Agent** (không cần API key ngoài).
Agent sẽ trực tiếp đọc thư mục `Inbox_Book/`, phân tích tên file, và di chuyển sách vào đúng folder trong thư viện.

## Cấu trúc Skill

```
.agents/skills/auto-organize/
├── SKILL.md                          # File này — hướng dẫn cho Agent
├── prompts/
│   └── classify_book.md              # Quy tắc phân loại sách
└── config/
    └── settings.json                 # Cấu hình (inbox dir, extensions...)
```

## Quy trình thực thi (dành cho Agent)

Khi user gọi `/auto-organize` hoặc yêu cầu phân loại sách, Agent phải thực hiện **đúng** các bước sau:

### Bước 1: Đọc cấu hình

Đọc file `config/settings.json` để biết:

- Tên thư mục inbox (`inbox_dir`)
- Các extension được hỗ trợ (`book_extensions`)

### Bước 2: Quét Inbox

Liệt kê tất cả file trong thư mục `Inbox_Book/` (hoặc tên khác theo config).
Chỉ xử lý file có extension `.pdf` hoặc `.epub`.

### Bước 3: Đọc cấu trúc thư viện hiện tại

Liệt kê toàn bộ thư mục cấp 1 (category) và cấp 2 (topic) để biết các folder đang có:

```bash
ls -d */
```

Cấu trúc hiện tại:

```
1_Computer_Science_Fundamentals/
├── Data_Structures_and_Algorithms/
├── Programming_Languages/
│   ├── Java/
│   └── JavaScript/
└── Systems_and_OS/

2_Software_Engineering_Disciplines/
├── Database/
├── DevOps/
├── Game_Development/
└── Software_Architecture_and_Design/

3_Career_and_Professional_Development/
├── Interview_Prep/
└── Job_Search_and_Career_Growth/

4_Miscellaneous/
└── English_Learning/

5_University_Courses/
├── Database_Administration/
├── E_Commerce/
└── PTTKHT_Systems_Analysis_and_Design/
```

### Bước 4: Phân loại từng cuốn sách

Đọc file `prompts/classify_book.md` để nắm quy tắc phân loại.

Dựa vào **tên file** để phân tích:

- Ngôn ngữ (tiếng Việt → University Courses)
- Chủ đề (Java, System Design, DevOps, v.v.)
- Loại sách (textbook, interview prep, career guide, v.v.)

Xác định:

- `category_folder`: Folder cấp 1 phù hợp nhất
- `topic_folder`: Folder cấp 2 (hoặc cấp 3) phù hợp nhất
- Nếu không có folder phù hợp → đề xuất tạo mới (Snake_Case)

### Bước 5: Báo cáo cho user

Hiển thị bảng phân loại cho user xem trước:

```
📖 File: "Clean Code.pdf"
   → 2_Software_Engineering_Disciplines/Software_Architecture_and_Design/
   💭 Reasoning: ...
```

### Bước 6: Di chuyển file (sau khi user xác nhận)

Di chuyển file bằng lệnh:

```bash
mv "Inbox_Book/filename.pdf" "category/topic/filename.pdf"
```

### Bước 7: Ghi log

Ghi thông tin vào `auto_organize.log`.

## Quy tắc quan trọng

1. **LUÔN hỏi user xác nhận** trước khi di chuyển file
2. **Đọc `prompts/classify_book.md`** trước khi phân loại
3. **Quét lại cấu trúc thư mục** mỗi lần chạy (có thể có folder mới)
4. **Ưu tiên folder có sẵn** — chỉ đề xuất tạo mới khi thực sự cần
5. **Di chuyển từng file một** — không batch move
