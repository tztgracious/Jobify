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
