#!/usr/bin/env python3
"""Remove password encryption from PDF files in Inbox."""

from __future__ import annotations

import argparse
import getpass
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lib.output import emit_json

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# Local password files are tried in order when no env var / --password-file is set.
# Prefer the dedicated unlock file; also accept project .env (common user expectation).
DEFAULT_PASSWORD_FILES = (".env.pdf-unlock", ".env")
PASSWORD_ENV_VARS = ("PDF_UNLOCK_PASSWORD", "PDF_PASSWORD")


@dataclass
class PdfResult:
    """Result for a single PDF."""

    path: str
    status: str
    message: str
    backup_path: str | None = None


def import_fitz():
    """Import PyMuPDF with a clear error if it is missing."""
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required. Install dependencies with: "
            "python -m pip install -r requirements.txt"
        ) from exc
    return fitz


def strip_wrapping_quotes(value: str) -> str:
    """Remove one matching pair of shell-style wrapping quotes."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def read_password_file(path: Path) -> str:
    """Read a password from a raw text file or simple env-style file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    raw_candidates: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "=" in stripped:
            key, value = stripped.split("=", 1)
            if key.strip() in PASSWORD_ENV_VARS:
                password = strip_wrapping_quotes(value)
                if password:
                    return password
            continue

        raw_candidates.append(stripped)

    if raw_candidates:
        return raw_candidates[0]

    raise ValueError(f"Password file is empty or missing {PASSWORD_ENV_VARS[0]}")


def resolve_password(
    base_dir: Path,
    password_file: str | None,
    *,
    prompt: bool,
) -> tuple[str | None, str]:
    """Resolve the PDF password without hardcoding it in this script.

    Resolution order:
    1. Process environment: PDF_UNLOCK_PASSWORD or PDF_PASSWORD
    2. Explicit --password-file
    3. Local files under base-dir: .env.pdf-unlock, then .env
    4. Interactive prompt (execute mode only, when stdin is a TTY)
    """
    for env_var in PASSWORD_ENV_VARS:
        password = os.environ.get(env_var)
        if password:
            return password, f"environment variable {env_var}"

    if password_file:
        path = Path(password_file)
        if not path.is_absolute():
            path = base_dir / path
        if not path.exists():
            raise FileNotFoundError(f"Password file not found: {path}")
        return read_password_file(path), str(path)

    for name in DEFAULT_PASSWORD_FILES:
        default_path = base_dir / name
        if default_path.exists():
            try:
                return read_password_file(default_path), str(default_path)
            except ValueError:
                # File exists but has no unlock password key; try next source.
                continue

    if prompt:
        if not sys.stdin.isatty():
            raise RuntimeError(
                "No password source found. Set PDF_UNLOCK_PASSWORD, or create "
                f"{DEFAULT_PASSWORD_FILES[0]} / .env with "
                f"{PASSWORD_ENV_VARS[0]}=... locally."
            )
        password = getpass.getpass("PDF password: ")
        if not password:
            raise RuntimeError("Password cannot be empty")
        return password, "interactive prompt"

    return None, "not provided"


def iter_pdfs(inbox_dir: Path) -> list[Path]:
    """Return PDF files directly under the requested Inbox directory."""
    if not inbox_dir.exists():
        raise FileNotFoundError(f"Inbox directory not found: {inbox_dir}")
    if not inbox_dir.is_dir():
        raise NotADirectoryError(f"Inbox path is not a directory: {inbox_dir}")
    return sorted(path for path in inbox_dir.iterdir() if path.suffix.lower() == ".pdf")


def resolve_inbox_dir(base_dir: Path, inbox_arg: str) -> Path:
    """Resolve and validate an Inbox directory under the project root."""
    inbox_dir = Path(inbox_arg)
    if not inbox_dir.is_absolute():
        inbox_dir = base_dir / inbox_dir

    inbox_dir = inbox_dir.resolve()
    try:
        inbox_dir.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError(f"--inbox-dir must be inside --base-dir: {inbox_dir}") from exc

    return inbox_dir


def authenticate(doc, password: str) -> bool:
    """Authenticate an encrypted PDF document."""
    result = doc.authenticate(password)
    return bool(result)


def inspect_pdf(pdf_path: Path, password: str | None, base_dir: Path) -> PdfResult:
    """Inspect one PDF during dry-run."""
    fitz = import_fitz()
    rel_path = pdf_path.relative_to(base_dir).as_posix()

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:  # PyMuPDF uses several exception classes.
        return PdfResult(rel_path, "failed", f"Cannot open PDF: {exc}")

    try:
        if not doc.needs_pass:
            return PdfResult(rel_path, "skipped", "PDF is not password-protected")

        if password is None:
            return PdfResult(rel_path, "planned", "Password-protected PDF")

        if authenticate(doc, password):
            return PdfResult(rel_path, "planned", "Password works; PDF can be unlocked")
        return PdfResult(rel_path, "failed", "Password did not unlock this PDF")
    finally:
        doc.close()


def make_backup_path(base_dir: Path, pdf_path: Path, batch_id: str) -> Path:
    """Build a backup path under .backups preserving relative location."""
    rel_path = pdf_path.relative_to(base_dir)
    return base_dir / ".backups" / "pdf_unlock" / batch_id / rel_path


def unlock_pdf(
    pdf_path: Path,
    password: str,
    base_dir: Path,
    *,
    batch_id: str,
    keep_backup: bool,
) -> PdfResult:
    """Unlock one encrypted PDF by replacing it with an unencrypted copy."""
    fitz = import_fitz()
    rel_path = pdf_path.relative_to(base_dir).as_posix()
    temp_path = pdf_path.with_name(f".{pdf_path.stem}.unlocking{pdf_path.suffix}")

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        return PdfResult(rel_path, "failed", f"Cannot open PDF: {exc}")

    backup_path: Path | None = None
    try:
        if not doc.needs_pass:
            return PdfResult(rel_path, "skipped", "PDF is not password-protected")

        if not authenticate(doc, password):
            return PdfResult(rel_path, "failed", "Password did not unlock this PDF")

        if temp_path.exists():
            temp_path.unlink()

        doc.save(
            temp_path,
            garbage=4,
            deflate=True,
            clean=True,
            encryption=fitz.PDF_ENCRYPT_NONE,
        )
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        return PdfResult(rel_path, "failed", f"Failed to write unlocked PDF: {exc}")
    finally:
        doc.close()

    try:
        verify = fitz.open(temp_path)
        try:
            if verify.needs_pass:
                temp_path.unlink()
                return PdfResult(rel_path, "failed", "Unlocked output is still encrypted")
        finally:
            verify.close()

        if keep_backup:
            backup_path = make_backup_path(base_dir, pdf_path, batch_id)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pdf_path, backup_path)

        os.replace(temp_path, pdf_path)
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        return PdfResult(rel_path, "failed", f"Failed to replace original PDF: {exc}")

    backup_rel = backup_path.relative_to(base_dir).as_posix() if backup_path else None
    return PdfResult(rel_path, "unlocked", "Password removed", backup_rel)


def print_results(results: list[PdfResult], *, dry_run: bool, password_source: str) -> None:
    """Print a human-readable summary."""
    print("=" * 60)
    print("My Bookshelves PDF Unlocker")
    print("=" * 60)
    print(f"Mode: {'dry-run' if dry_run else 'execute'}")
    print(f"Password source: {password_source}")
    print()

    if not results:
        print("No PDF files found.")
        return

    for result in results:
        print(f"- [{result.status}] {result.path}: {result.message}")
        if result.backup_path:
            print(f"  backup: {result.backup_path}")

    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1

    print()
    print("Summary:")
    for status in sorted(counts):
        print(f"- {status}: {counts[status]}")

    if dry_run:
        print()
        print("No files changed. Add --execute to replace encrypted PDFs.")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", default=".", help="Project root directory")
    parser.add_argument("--inbox-dir", default="Inbox", help="Inbox directory under base-dir")
    parser.add_argument(
        "--password-file",
        help=(
            "Local password file. Supports raw password text or "
            "PDF_UNLOCK_PASSWORD=... format. Default: .env.pdf-unlock, then .env."
        ),
    )
    parser.add_argument("--execute", action="store_true", help="Replace encrypted PDFs")
    parser.add_argument("--no-backup", action="store_true", help="Do not keep encrypted backups")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first failure")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    try:
        inbox_dir = resolve_inbox_dir(base_dir, args.inbox_dir)
        password, password_source = resolve_password(
            base_dir,
            args.password_file,
            prompt=args.execute,
        )
        pdfs = iter_pdfs(inbox_dir)
    except Exception as exc:
        if args.json:
            emit_json({"ok": False, "error": str(exc)})
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    results: list[PdfResult] = []
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    for pdf_path in pdfs:
        if args.execute:
            if password is None:
                raise RuntimeError("Password is required in execute mode")
            result = unlock_pdf(
                pdf_path,
                password,
                base_dir,
                batch_id=batch_id,
                keep_backup=not args.no_backup,
            )
        else:
            result = inspect_pdf(pdf_path, password, base_dir)

        results.append(result)
        if args.fail_fast and result.status == "failed":
            break

    ok = all(result.status != "failed" for result in results)

    if args.json:
        emit_json(
            {
                "ok": ok,
                "dry_run": not args.execute,
                "password_source": password_source,
                "results": [result.__dict__ for result in results],
            }
        )
    else:
        print_results(results, dry_run=not args.execute, password_source=password_source)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
