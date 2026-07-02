import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import cli  # noqa: E402


class CliTests(unittest.TestCase):
    def test_unlock_pdfs_command_is_registered(self) -> None:
        self.assertEqual(cli.COMMANDS["unlock-pdfs"]["script"], "unlock_pdfs.py")

    def test_epub_to_pdf_command_is_registered(self) -> None:
        self.assertEqual(cli.COMMANDS["epub-to-pdf"]["script"], "epub_to_pdf.py")

    def test_pdf_to_epub_command_is_registered(self) -> None:
        self.assertEqual(cli.COMMANDS["pdf-to-epub"]["script"], "pdf_to_epub.py")

    def test_doctor_aliases_route_to_doctor(self) -> None:
        self.assertEqual(cli.COMMANDS["doctor"]["script"], "doctor.py")
        self.assertEqual(cli.COMMANDS["validate"]["script"], "doctor.py")
        self.assertEqual(cli.normalize_command("docter"), "doctor")
        self.assertEqual(cli.normalize_command("doc"), "doctor")

    def test_unlock_aliases_route_to_unlock_pdfs(self) -> None:
        self.assertEqual(cli.normalize_command("unlock"), "unlock-pdfs")
        self.assertEqual(cli.normalize_command("pdf-unlock"), "unlock-pdfs")

    def test_epub_aliases_route_to_epub_to_pdf(self) -> None:
        self.assertEqual(cli.normalize_command("epub2pdf"), "epub-to-pdf")
        self.assertEqual(cli.normalize_command("epubtopdf"), "epub-to-pdf")
        self.assertEqual(cli.normalize_command("convert-epub"), "epub-to-pdf")
        self.assertEqual(cli.normalize_command("convert-epubs"), "epub-to-pdf")

    def test_pdf_aliases_route_to_pdf_to_epub(self) -> None:
        self.assertEqual(cli.normalize_command("pdf2epub"), "pdf-to-epub")
        self.assertEqual(cli.normalize_command("pdftoepub"), "pdf-to-epub")
        self.assertEqual(cli.normalize_command("convert-pdf"), "pdf-to-epub")
        self.assertEqual(cli.normalize_command("convert-pdfs"), "pdf-to-epub")


if __name__ == "__main__":
    unittest.main()
