# AGENTS.md

Huong dan nay la entrypoint cho Codex khi lam viec trong repo My-Bookshelves.
Thu muc `.agents/` van la nguon dung chung cho ca Antigravity va Codex.
Thu muc `.codex/` la adapter rieng cho Codex va chi tro ve `.agents/`.

## Load Order

1. Luon doc `.agents/rules/my-bookshelves.md` truoc khi sua code, metadata, sach, cover, upload, hoac workflow.
2. Khi user goi `/auto-organize`, `auto-organize`, hoac yeu cau phan loai sach trong `Inbox/`, doc:
   - `.codex/manifest.json`
   - `.codex/rules.md`
   - `.codex/workflows/auto-organize.md`
   - `.agents/workflows/auto-organize.md`
   - `.agents/skills/auto-organize/SKILL.md`
   - `.agents/skills/auto-organize/prompts/classify_book.md`
   - `.agents/skills/auto-organize/config/settings.json`
3. Neu chi sua frontend, van phai giu ranh gioi zero-dependency trong project rules.

## Codex Compatibility Map

| Antigravity concept | Codex equivalent |
| --- | --- |
| Slash workflow nhu `/auto-organize` | User co the goi bang text; doc file trong `.agents/workflows/` va thuc thi cac buoc |
| `view_file` | Dung cong cu doc file hoac `Get-Content -Raw` trong PowerShell |
| `multi_replace_file_content` | Dung `apply_patch` cho batch edit; voi JSON lon, uu tien tool/CLI san co va validate JSON sau khi sua |
| `// turbo` comment | Ghi chu toi uu tu Antigravity, khong phai syntax bat buoc voi Codex |
| Bash snippets | Chay tuong duong trong PowerShell khi o Windows (`Get-ChildItem`, `New-Item`, `Move-Item`) |

## Operating Rules For Codex

- Shell mac dinh la PowerShell, working directory la repo root.
- Dung `rg`/`rg --files` de tim file va noi dung.
- Khong commit file sach (`*.pdf`, `*.epub`, `*.docx`) vao git.
- Hoi user xac nhan mot lan truoc khi rename/move hang loat sach hoac upload that.
- Truoc khi chay `generate`, phai verify PyMuPDF, Pillow va python-docx dung interpreter.
- `python scripts/cli.py generate --base-dir .` chi chay mot lan cho moi batch; neu fail thi sua root cause truoc.
- Sau `generate`, bat buoc verify `download_url` va `topic` cua sach trong sub-folder.
- Khi ghi `category`/`topic` vao `site/data.json`, dung display name co khoang trang; khong ghi `Snake_Case`.
- Neu test/build/lint/runtime fail trong qua trinh lam viec, append vao `ERRORS.md` theo rule error logging cua workspace.

## Auto-Organize Summary

Quy trinh dung chung:

1. Quet `Inbox/` va dem N sach moi.
2. Dry-run rename, chi execute sau khi user dong y.
3. Generate va doc `library_structure.log`.
4. Phan loai tat ca sach trong bo nho, uu tien folder co san.
5. Hien mot bang tong hop va hoi user xac nhan mot lan.
6. Move batch vao `Books/`.
7. Verify dependencies, generate cover/data, chen descriptions, verify metadata.
8. Dry-run upload, upload that neu count dung N.
9. Cap nhat `library_structure.log`, commit/push neu workflow/user yeu cau.
