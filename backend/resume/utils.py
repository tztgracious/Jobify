import requests


def grammar_check(text):
    response = requests.post(
        "https://api.languagetool.org/v2/check",
        data={"text": text, "language": "en-US"}
    )
    return response.json()


def get_keywords_using_openai(text):
    # call OpenAI API here to extract keywords
    pass


def get_file_size_mb(file_size_bytes):
    """Convert bytes to MB for user display"""
    return round(file_size_bytes / (1024 * 1024), 2)

# TODO: get better error message. Rerun a Response object if invalid
def check_file_size_with_message(file, max_size_mb=5):
    """Check file size with user-friendly message"""
    max_size_bytes = max_size_mb * 1024 * 1024

    if file.size > max_size_bytes:
        current_size = get_file_size_mb(file.size)
        return False, f"File size ({current_size} MB) exceeds limit ({max_size_mb} MB)"

    return True, None

from llama_cloud_services import LlamaParse

parser = LlamaParse(
    api_key="llx-...",  # can also be set in your env as LLAMA_CLOUD_API_KEY
    num_workers=4,       # if multiple files passed, split in `num_workers` API calls
    verbose=True,
    language="en",       # optionally define a language, default=en
)

# sync
result = parser.parse("./my_file.pdf")

# sync batch
results = parser.parse(["./my_file1.pdf", "./my_file2.pdf"])

# get the llama-index markdown documents
markdown_documents = result.get_markdown_documents(split_by_page=True)

# get the llama-index text documents
text_documents = result.get_text_documents(split_by_page=False)

# get the image documents
image_documents = result.get_image_documents(
    include_screenshot_images=True,
    include_object_images=False,
    # Optional: download the images to a directory
    # (default is to return the image bytes in ImageDocument objects)
    image_download_dir="./images",
)

# access the raw job result
# Items will vary based on the parser configuration
for page in result.pages:
    print(page.text)
    print(page.md)
    print(page.images)
    print(page.layout)
    print(page.structuredData)