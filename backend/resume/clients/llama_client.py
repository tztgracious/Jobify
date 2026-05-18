import os
from django.conf import settings
from llama_cloud_services import LlamaParse
from jobify_backend.logger import logger

class LlamaClient:
    """
    Client for interacting with LlamaParse for PDF resume parsing.
    """
    
    def __init__(self):
        self.api_key = os.getenv("LLAMA_PARSE_API_KEY")
        if not self.api_key:
            logger.error("LLAMA_PARSE_API_KEY not found in environment")
            
    def parse_pdf(self, file_path: str) -> str:
        """
        Parses a PDF file and returns the extracted text.
        """
        if not self.api_key:
            raise Exception("LlamaParse API key is missing")

        # Resolve path if relative
        if not os.path.isabs(file_path):
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        else:
            full_path = file_path

        if not os.path.exists(full_path):
            logger.error(f"File not found for parsing: {full_path}")
            raise FileNotFoundError(f"Resume file not found: {full_path}")

        try:
            logger.info(f"Starting LlamaParse for file: {full_path}")
            parser = LlamaParse(
                api_key=self.api_key,
                num_workers=4,
                verbose=False,
                language="en",
            )
            
            # Sync parsing
            result = parser.parse(full_path)
            
            # Extract text from the first page (as per existing logic)
            if hasattr(result, 'pages') and len(result.pages) > 0:
                return result.pages[0].text
            else:
                logger.warning(f"LlamaParse returned no pages for: {full_path}")
                return ""
                
        except Exception as e:
            logger.error(f"LlamaParse failed: {e}")
            raise Exception(f"Failed to parse PDF with LlamaParse: {e}")
