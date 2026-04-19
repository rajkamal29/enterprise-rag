"""Document Intelligence-based PDF, DOCX, and HTML parsing."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocumentParser:
    """Parse documents using Azure Document Intelligence."""

    def __init__(self, client: Any) -> None:
        """Initialize Document Intelligence parser.
        
        Args:
            client: DocumentIntelligenceClient instance from AzureClientFactory
        """
        self.client = client

    def parse_document(self, file_path: str | Path) -> dict[str, object]:
        """Parse a document and extract text with structure.
        
        Args:
            file_path: Path to PDF, DOCX, or HTML file
            
        Returns:
            Dict with extracted content and metadata
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        file_ext = file_path.suffix.lower()

        if file_ext == ".pdf":
            return self._parse_pdf(file_path)
        elif file_ext in [".docx", ".doc"]:
            return self._parse_docx(file_path)
        elif file_ext in [".html", ".htm"]:
            return self._parse_html(file_path)
        elif file_ext in [".txt", ".md"]:
            return self._parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def _parse_pdf(self, file_path: Path) -> dict[str, object]:
        """Parse PDF using Document Intelligence."""
        logger.info(f"Parsing PDF: {file_path.name}")
        
        with open(file_path, "rb") as f:
            poller = self.client.begin_analyze_document("prebuilt-document", f)
        
        result = poller.result()
        
        return {
            "source": str(file_path),
            "format": "pdf",
            "title": file_path.stem,
            "content": self._extract_text_from_result(result),
            "pages": len(result.pages) if result.pages else 0,
            "metadata": {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
            },
        }

    def _parse_docx(self, file_path: Path) -> dict[str, object]:
        """Parse DOCX using Document Intelligence."""
        logger.info(f"Parsing DOCX: {file_path.name}")
        
        with open(file_path, "rb") as f:
            poller = self.client.begin_analyze_document("prebuilt-document", f)
        
        result = poller.result()
        
        return {
            "source": str(file_path),
            "format": "docx",
            "title": file_path.stem,
            "content": self._extract_text_from_result(result),
            "pages": len(result.pages) if result.pages else 1,
            "metadata": {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
            },
        }

    def _parse_text(self, file_path: Path) -> dict[str, object]:
        """Parse plain text or markdown file."""
        logger.info(f"Parsing text: {file_path.name}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "source": str(file_path),
            "format": file_path.suffix.lstrip("."),
            "title": file_path.stem,
            "content": content,
            "pages": 1,
            "metadata": {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
            },
        }

    def _parse_html(self, file_path: Path) -> dict[str, object]:
        """Parse HTML file (extract text content)."""
        logger.info(f"Parsing HTML: {file_path.name}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Simple HTML text extraction (remove tags)
        import re
        text = re.sub("<[^<]+?>", "", content)
        text = re.sub(r"\s+", " ", text).strip()
        
        return {
            "source": str(file_path),
            "format": "html",
            "title": file_path.stem,
            "content": text,
            "pages": 1,
            "metadata": {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
            },
        }

    @staticmethod
    def _extract_text_from_result(result: object) -> str:
        """Extract plain text from Document Intelligence result."""
        if hasattr(result, "content") and result.content:
            text: str = result.content
            return text
        
        # Fallback: concatenate paragraphs if available
        text_parts: list[str] = []
        if hasattr(result, "paragraphs") and result.paragraphs:
            for para in result.paragraphs:
                if hasattr(para, "content"):
                    text_parts.append(para.content)
        
        return "\n".join(text_parts) if text_parts else ""
