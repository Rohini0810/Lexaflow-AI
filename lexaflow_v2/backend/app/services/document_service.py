from pathlib import Path

from pypdf import PdfReader

from backend.app.core.config import settings

try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
except Exception:  # pragma: no cover
    DocumentIntelligenceClient = None
    AzureKeyCredential = None


def _extract_with_pypdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    chunks: list[str] = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks).strip()


def _extract_with_azure(file_path: Path) -> str:
    if DocumentIntelligenceClient is None or AzureKeyCredential is None:
        raise RuntimeError("Azure Document Intelligence SDK unavailable")

    endpoint = settings.azure_doc_intelligence_endpoint
    key = settings.azure_doc_intelligence_key
    if not endpoint or not key:
        raise RuntimeError("Azure Document Intelligence credentials missing")

    client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    with file_path.open("rb") as handle:
        poller = client.begin_analyze_document(model_id="prebuilt-read", body=handle)
        result = poller.result()

    lines: list[str] = []
    for page in result.pages:
        for line in page.lines:
            lines.append(line.content)
    return "\n".join(lines).strip()


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        try:
            return _extract_with_azure(path)
        except Exception:
            return _extract_with_pypdf(path)

    raise ValueError(f"Unsupported file format: {suffix}. Use .pdf or .txt")


