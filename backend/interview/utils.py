import json
import os

import requests
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
)

from jobify_backend.logger import logger


def get_questions_using_openai(session):
    target_job = session.target_job
    keywords = session.keywords

    prompt = f"""
    You are a professional career coach helping job seekers prepare for interviews.

    Given the following target job and list of relevant keywords from a candidate's resume, generate one technical question and three general interview questions that a candidate might be asked for this role. The technical question should focus on evaluating the candidate’s hands-on skills or conceptual understanding, while the interview questions should evaluate communication, problem-solving, and fit for the role.

    Target Job: {target_job}
    Keywords: {', '.join(keywords)}

    Return ONLY a valid JSON object with this format:
    {{
      "tech_question": ["Tech Question 1"],
      "interview_question": ["Interview Question 1", "Interview Question 2", "Interview Question 3"]
    }}

    Do not include any explanations, formatting, or markdown. Only return the raw JSON object.
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
        session.questions = questions["interview_question"]
        logger.info(f"Interview questions generated: {session.questions}")
        session.tech_questions = questions["tech_question"]
        logger.info(f"Technical questions generated: {session.tech_questions}")
        session.save()
        logger.info(f"Questions extracted for session: {session.id}")
    except json.JSONDecodeError:
        print(f"Error parsing questions: {response_text}")



def get_feedback_using_openai_text(resume, interview_session):
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


def extract_audio_from_video(video_file):
    """
    Extract audio from video file and return the path to the temporary audio file.
    Returns None if extraction fails.
    """
    import subprocess
    import tempfile

    try:
        # Create a temporary file for the extracted audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name

        # Extract audio from video using ffmpeg
        # This command extracts audio and converts it to MP3
        ffmpeg_command = [
            'ffmpeg',
            '-i', video_file.temporary_file_path(),  # Input video file
            '-vn',  # No video
            '-acodec', 'mp3',  # Audio codec
            '-ar', '16000',  # Sample rate (16kHz is good for speech recognition)
            '-ac', '1',  # Mono audio
            '-y',  # Overwrite output file
            temp_audio_path
        ]

        # Run ffmpeg command
        subprocess.run(ffmpeg_command, check=True, capture_output=True)

        return temp_audio_path

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        return None
    except Exception as e:
        print(f"Audio extraction exception: {e}")
        return None


def audio_transcription(video_file):
    """
    Transcribe audio from the uploaded video file using a speech-to-text API.
    """
    try:
        # Extract audio from video
        temp_audio_path = extract_audio_from_video(video_file)
        if not temp_audio_path:
            return None

        # STEP 1 Create a Deepgram client using the API key from environment
        deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

        # Read the extracted audio file
        with open(temp_audio_path, "rb") as file:
            buffer_data = file.read()

        payload = {
            "buffer": buffer_data,
        }

        # STEP 2: Configure Deepgram options for audio analysis
        options = PrerecordedOptions(
            model="nova-3",
            smart_format=True,
            filler_words=True,
            punctuate=True,
            measurements=True,
            language="en-US",
            diarize=True,  # Can help with speech analysis
        )

        # STEP 3: Call the transcribe_file method with the text payload and options
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

        # Clean up temporary file
        os.unlink(temp_audio_path)

        return response

    except Exception as e:
        print(f"Transcription exception: {e}")
        return None


def get_feedback_video(video_file, doc_id):
    """
    Process the uploaded video file, extract audio, and get feedback using OpenAI.
    Returns a dictionary with feedback or an error message.
    """
    try:
        # Extract audio from video
        temp_audio_path = extract_audio_from_video(video_file)
        if not temp_audio_path:
            return {"error": "Failed to extract audio from video file."}

        # TODO: Implement feedback retrieval using OpenAI

        return "feedback"

    except Exception as e:
        print(f"Error processing video file: {e}")
        return {"error": "An error occurred while processing the video file."}
