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


def parse_resume_with_llama(file):
    # call LlamaParse API here
    pass
