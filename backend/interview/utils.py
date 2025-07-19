import json
import os

import requests


def get_questions_using_openai(target_job, keywords):
    prompt = f"""
        You are a professional career coach helping job seekers prepare for interviews.

        Given the following target job and keywords, generate 3 relevant interview questions that a candidate might be asked. These questions should be realistic, challenging, and commonly asked in interviews for this role.

        Target Job: {target_job}
        Keywords: {', '.join(keywords)}

        Return ONLY a valid JSON list of 3 strings. Do not include any explanation, formatting, or markdown. Example format:
        [
          "First question?",
          "Second question?",
          "Third question?"
        ]
        """
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPEN_ROUTER_API_KEY')}",
            "Content-Type": "application/json",
            "HTTP-Referer": "jobify.com",
            "X-Title": "Jobify",
        },
        data=json.dumps({
            "model": "openai/gpt-4o",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )
    response_text = response.json()["choices"][0]["message"]["content"]
    try:
        questions = json.loads(response_text)
    except json.JSONDecodeError:
        print(f"Error parsing questions: {response_text}")
        return []
    return questions


def get_feedback_using_openai(resume, interview_session):
    questions = interview_session.questions
    answers = interview_session.answers
    prompt = f"""
        You are a professional interview coach.

    A candidate is applying for the role of: "{resume.target_job}"

    Their resume contains the following keywords:
    {', '.join(resume.keywords)}

    They were asked these interview questions and provided the following answers:

    Question 1: "{questions[0]}"
    Answer 1: "{answers[0]}"

    Question 2: "{questions[1]}"
    Answer 2: "{answers[1]}"

    Question 3: "{questions[2]}"
    Answer 3: "{answers[2]}"

    Please provide structured feedback in this **strict JSON** format:

    {{
      "question_1_feedback": "Your feedback here",
      "question_2_feedback": "Your feedback here",
      "question_3_feedback": "Your feedback here",
      "summary": "Overall impression and actionable tips"
    }}

    Rules:
    - **Do not include any Markdown formatting such as triple backticks. Only return raw JSON.**
    - Do not include explanations outside the JSON.
    - Feedback should be constructive, detailed, and professional.
    - Use only double quotes and valid JSON syntax.

"""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPEN_ROUTER_API_KEY')}",
            "Content-Type": "application/json",
            "HTTP-Referer": "jobify.com",
            "X-Title": "Jobify",
        },
        data=json.dumps({
            "model": "openai/gpt-4o",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )
    response_text = response.json()["choices"][0]["message"]["content"]
    try:
        feedbacks = json.loads(response_text)
    except json.JSONDecodeError:
        print(f"Error parsing feedback: {response_text}")
        return []
    return feedbacks
