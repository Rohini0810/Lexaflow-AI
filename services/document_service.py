from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import os

# Create client
def get_client():
    endpoint = os.getenv("DOC_INTELLIGENCE_ENDPOINT")
    key = os.getenv("DOC_INTELLIGENCE_KEY")

    if not endpoint or not key:
        raise ValueError("Missing DOC_INTELLIGENCE credentials")

    return DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

# Extract text
def extract_text_from_pdf(file_path):
    client = get_client()

    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document(
            model_id="prebuilt-read",
            body=f
        )
        result = poller.result()

    text = ""

    for page in result.pages:
        for line in page.lines:
            text += line.content + "\n"

    return text