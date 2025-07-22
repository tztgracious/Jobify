import json
import os

import requests
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
)
from rest_framework.response import Response

from interview.models import InterviewSession
from jobify_backend.logger import logger
import os
import uuid
from django.conf import settings
from jobify_backend.logger import logger
from jobify_backend.settings import MAX_VIDEO_FILE_SIZE
    
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
        session.tech_questions = questions["tech_question"]
        session.question_status = InterviewSession.Status.COMPLETE
        session.save()
    except json.JSONDecodeError:
        print(f"Error parsing questions: {response_text}")


def get_feedback_using_openai_text(interview_session):
    questions = interview_session.questions
    answers = interview_session.answers
    tech_questions = interview_session.tech_questions
    tech_answers = interview_session.tech_answers
    target_job = interview_session.target_job
    keywords = interview_session.keywords
    prompt = f"""
    You are a professional interview coach.

    A candidate is applying for the role of: "{target_job}"

    Their resume contains the following keywords:
    {', '.join(keywords)}

    They were asked these interview questions and provided the following answers:
    
    Tech Question: "{tech_questions[0]}"
    Tech Answer: "{tech_answers[0]}"

    Interview Question 1: "{questions[0]}"
    Interview Answer 1: "{answers[0]}"

    Interview Question 2: "{questions[1]}"
    Interview Answer 2: "{answers[1]}"

    Interview Question 3: "{questions[2]}"
    Interview Answer 3: "{answers[2]}"

    Please provide structured feedback in this **strict JSON** format:

    {{
      "tech_question_feedback": "Your feedback here",
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


def get_feedback_using_openai_video(interview_session):
    questions = interview_session.questions
    answers = interview_session.answers
    tech_questions = interview_session.tech_questions
    tech_answers = interview_session.tech_answers
    target_job = interview_session.target_job
    keywords = interview_session.keywords
    prompt = f"""
    You are a professional interview coach.
    """
    return Response({"error": "Not implemented yet. Please use text feedback for now."}, status=501)

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


def process_text_answer(session_id, question_index, question_text, answer, interview_session):
    """
    Process a text answer for an interview question.
    
    Args:
        session_id (str): The interview session ID
        question_index (int): Index of the question being answered
        question_text (str): The question text for validation
        answer (str): The text answer provided
        interview_session (InterviewSession): The interview session object
        
    Returns:
        dict: Response data containing answer information and status
    """
    
    
    # Validate that the question text matches the stored question
    stored_question = interview_session.questions[question_index]
    if question_text.strip() != stored_question.strip():
        logger.warning(f"Question mismatch for id {session_id}, question_index {question_index}")
        return {
            "error": "Question text does not match the stored question",
            "expected_question": stored_question,
            "provided_question": question_text,
            "status": 400
        }

    # Initialize answers list if needed (pad with empty strings)
    if len(interview_session.answers) < len(interview_session.questions):
        interview_session.answers = [''] * len(interview_session.questions)

    # Update the specific answer
    interview_session.answers[question_index] = answer

    # Check if all questions are answered
    answered_count = len([ans for ans in interview_session.answers if ans and ans.strip()])
    is_completed = answered_count == len(interview_session.questions)
    interview_session.is_completed = is_completed

    interview_session.save()

    logger.info(f"Updated interview session for id {session_id} - answered question {question_index} with text answer")

    # Return success response data
    return {
        "id": session_id,
        "message": f"Text answer submitted for question {question_index + 1}",
        "question": stored_question,
        "answer_type": "text",
        "answer": answer,
        "progress": interview_session.progress,
        "is_completed": is_completed,
        "status": 200
    }


def process_video_answer(session_id, question_index, question_text, video_file, interview_session):
    """
    Process a video answer for an interview question.
    
    Args:
        session_id (str): The interview session ID
        question_index (int): Index of the question being answered
        video_file: The uploaded video file
        question_text (str): The question text for validation
        interview_session (InterviewSession): The interview session object
        
    Returns:
        dict: Response data containing video information and status
    """

    
    # Validate video file size
    if video_file.size > MAX_VIDEO_FILE_SIZE:
        logger.warning(f"Video file too large for id {session_id}: {video_file.size} bytes")
        return {
            "error": f"Video file size too large. Maximum allowed size is 75MB, but received {video_file.size / (1024 * 1024):.1f}MB",
            "status": 413
        }

    # Validate that the question text matches the stored question
    stored_question = interview_session.questions[question_index]
    if question_text.strip() != stored_question.strip():
        logger.warning(f"Question mismatch for id {session_id}, question_index {question_index}")
        return {
            "error": "Question text does not match the stored question",
            "expected_question": stored_question,
            "provided_question": question_text,
            "status": 400
        }

    # Create videos directory if it doesn't exist
    video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos')
    os.makedirs(video_dir, exist_ok=True)

    # Generate unique filename for the video answer
    file_extension = os.path.splitext(video_file.name)[1]
    unique_filename = f"{session_id}_q{question_index}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(video_dir, unique_filename)

    try:
        # Save the video file
        with open(file_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        # Store the relative path as the answer
        video_path = f"videos/{unique_filename}"
        logger.info(f"Video answer saved for id {session_id}, question {question_index}: {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save video answer for id {session_id}, question {question_index}: {str(e)}")
        return {
            "error": "Failed to save video file",
            "status": 500
        }

    # Initialize answers list if needed (pad with empty strings)
    if len(interview_session.answers) < len(interview_session.questions):
        interview_session.answers = [''] * len(interview_session.questions)

    # Update the specific answer
    interview_session.answers[question_index] = video_path

    # Check if all questions are answered
    answered_count = len([ans for ans in interview_session.answers if ans and ans.strip()])
    is_completed = answered_count == len(interview_session.questions)
    interview_session.is_completed = is_completed

    interview_session.save()

    logger.info(f"Updated interview session for id {session_id} - answered question {question_index} with video answer")

    # Return success response data
    return {
        "id": session_id,
        "message": f"Video answer submitted for question {question_index + 1}",
        "question": stored_question,
        "answer_type": "video",
        "video_path": video_path,
        "video_filename": video_file.name,
        "video_size": video_file.size,
        "progress": interview_session.progress,
        "is_completed": is_completed,
        "status": 200
    }
