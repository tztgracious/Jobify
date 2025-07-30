import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

import requests
from requests import session

from interview.models import InterviewSession
from interview.multi_agent import BaseAgent, InterviewerRole
from jobify_backend.logger import logger

def get_questions_using_openai(interview_session):
    target_job = interview_session.target_job
    keywords = interview_session.keywords

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
        data=json.dumps(
            {
                "model": "openai/gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
            }
        ),
    )
    response_text = response.json()["choices"][0]["message"]["content"]
    try:
        questions = json.loads(response_text)
        interview_session.questions = questions["interview_question"]
        interview_session.tech_questions = questions["tech_question"]
        interview_session.question_status = InterviewSession.Status.COMPLETE
        interview_session.save()
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
        data=json.dumps(
            {
                "model": "openai/gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
            }
        ),
    )
    response_text = response.json()["choices"][0]["message"]["content"]
    try:
        feedbacks = json.loads(response_text)
    except json.JSONDecodeError:
        print(f"Error parsing feedback: {response_text}")
        return []
    return feedbacks


def get_questions_using_openai_multi_agent(interview_session):
    """Multi-agent version that maintains the same interface as the original function"""
    api_key = os.getenv('OPEN_ROUTER_API_KEY')
    target_job = interview_session.target_job
    keywords = interview_session.keywords
    
    # Create one technical agent for tech question
    tech_agent = BaseAgent(InterviewerRole.TECHNICAL_LEAD, api_key)
    
    # Select 3 agents for interview questions based on job type
    selected_roles = _select_agent_roles_for_job(target_job, num_agents=3)
    interview_agents = [BaseAgent(role, api_key) for role in selected_roles]

    # Generate tech question and interview questions concurrently
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit tech question generation
        tech_future = executor.submit(_generate_tech_question, tech_agent, target_job, keywords)
        
        # Submit interview questions generation
        interview_futures = [
            executor.submit(agent.generate_question_sync, target_job, keywords)
            for agent in interview_agents
        ]

        # Get tech question result
        tech_question_data = tech_future.result()
        tech_questions = [tech_question_data["question"]]
        
        # Get interview questions results
        questions_data = []
        for future in interview_futures:
            question_data = future.result()
            questions_data.append(question_data)

    # Sort interview questions by difficulty for better flow
    questions_data.sort(key=lambda q: q.get("difficulty", 3))
    interview_questions = [q["question"] for q in questions_data]
    
    # Save results to the database (same as original function)
    try:
        interview_session.questions = interview_questions
        interview_session.tech_questions = tech_questions
        interview_session.question_status = InterviewSession.Status.COMPLETE
        logger.info(f"Generated MA questions: {interview_questions} | Tech Questions: {tech_questions}")
        interview_session.save()
    except Exception as e:
        print(f"Error saving multi-agent questions: {e}")
        interview_session.question_status = InterviewSession.Status.FAILED
        interview_session.save()


def get_feedback_using_openai_multi_agent(interview_session):
    """Multi-agent version that maintains the same interface as the original function"""
    api_key = os.getenv('OPEN_ROUTER_API_KEY')
    
    questions = interview_session.questions
    answers = interview_session.answers
    tech_questions = interview_session.tech_questions or []
    tech_answers = interview_session.tech_answers or []
    target_job = interview_session.target_job
    keywords = interview_session.keywords

    # Combine tech and interview questions/answers with tech at the head
    all_questions = []
    all_answers = []
    
    # Add tech question/answer at the head if they exist
    if tech_questions and tech_answers and len(tech_questions) > 0 and len(tech_answers) > 0:
        all_questions.append(tech_questions[0])
        all_answers.append(tech_answers[0])
    
    # Add interview questions/answers
    all_questions.extend(questions)
    all_answers.extend(answers)

    # Get feedback from multiple agents for all questions
    all_feedbacks = []
    logger.debug(f"Starting multi-agent feedback for {len(all_questions)} questions")

    # For each question, get feedback from 2-3 different agents
    for i, (question, answer) in enumerate(zip(all_questions, all_answers)):
        if not answer.strip():  # Skip empty answers
            all_feedbacks.append([])
            continue
            
        # Select different agents for each question to get diverse perspectives
        # For tech questions (index 0), use more technical agents
        if i == 0 and tech_questions:  # First question is tech question
            reviewing_roles = [InterviewerRole.TECHNICAL_LEAD, InterviewerRole.SENIOR_PEER, InterviewerRole.INDUSTRY_EXPERT]
        else:
            reviewing_roles = _select_reviewing_roles(i)
            
        agents = [BaseAgent(role, api_key) for role in reviewing_roles]

        # Collect feedback from each agent
        question_feedback = []
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = [
                executor.submit(agent.evaluate_answer_sync, question, answer, target_job, keywords)
                for agent in agents
            ]

            for future in futures:
                feedback = future.result()
                question_feedback.append(feedback)

        all_feedbacks.append(question_feedback)

    # Synthesize feedback from all agents
    synthesized_feedback = _synthesize_feedback(all_questions, all_answers, all_feedbacks, target_job, keywords, api_key)

    # Format to match expected output
    feedback_questions = synthesized_feedback["question_feedback"]
    
    # Determine if we have tech feedback at the head
    has_tech = tech_questions and tech_answers and len(tech_questions) > 0 and len(tech_answers) > 0
    
    formatted_feedback = {
        "tech_question_feedback": feedback_questions[0] if has_tech and len(feedback_questions) > 0 else "",
        "question_1_feedback": feedback_questions[1] if has_tech and len(feedback_questions) > 1 else (feedback_questions[0] if len(feedback_questions) > 0 else ""),
        "question_2_feedback": feedback_questions[2] if has_tech and len(feedback_questions) > 2 else (feedback_questions[1] if len(feedback_questions) > 1 else ""),
        "question_3_feedback": feedback_questions[3] if has_tech and len(feedback_questions) > 3 else (feedback_questions[2] if len(feedback_questions) > 2 else ""),
        "summary": synthesized_feedback["summary"],
    }

    return formatted_feedback


def process_text_answer(session_id: str, question_index: int, question_text: str, answer: str, interview_session) -> Dict[str, Any]:
    """
    Process and save a text answer for an interview question.
    
    Args:
        session_id: The interview session ID
        question_index: Index of the question being answered (0-based)
        question_text: The actual question text for validation
        answer: The user's text answer
        interview_session: The InterviewSession model instance
    
    Returns:
        Dict with success/error information and status code
    """
    try:
        # Validate that the question text matches
        if question_index >= len(interview_session.questions):
            logger.warning(f"Invalid question_index {question_index} for session {session_id}")
            return {
                "error": f"question_index must be between 0 and {len(interview_session.questions) - 1}",
                "status": 400
            }
        
        if interview_session.questions[question_index] != question_text:
            logger.warning(f"Question mismatch at index {question_index} for session {session_id}")
            return {
                "error": "Question text does not match the question at the specified index",
                "status": 400
            }
        
        # Ensure answers list is properly sized
        answers = interview_session.answers or []
        while len(answers) <= question_index:
            answers.append("")
        
        # Update the answer at the specified index
        answers[question_index] = answer
        interview_session.answers = answers
        interview_session.save()
        
        # Calculate progress
        answered_questions = sum(1 for ans in answers if ans.strip())
        total_questions = len(interview_session.questions)
        progress = round((answered_questions / total_questions) * 100, 2) if total_questions > 0 else 0
        is_completed = answered_questions == total_questions
        
        logger.info(f"Updated interview session for id {session_id} - answered question {question_index} with text answer")
        
        return {
            "id": session_id,
            "message": f"Text answer submitted for question {question_index + 1}",
            "question": question_text,
            "answer_type": "text",
            "answer": answer,
            "progress": progress,
            "is_completed": is_completed,
            "status": 200
        }
        
    except Exception as e:
        logger.error(f"Error processing text answer for session {session_id}: {str(e)}")
        return {
            "error": "Failed to save text answer",
            "status": 500
        }


def _generate_tech_question(tech_agent: BaseAgent, target_job: str, keywords: List[str]) -> Dict[str, Any]:
    """Generate a technical question using the technical agent"""
    tech_prompt = f"""{tech_agent.personality}
    
    You're interviewing for: {target_job}
    Key technical skills/keywords: {', '.join(keywords)}
    
    Generate ONE technical question that evaluates hands-on skills or conceptual understanding.
    The question should focus on practical implementation, problem-solving, or technical concepts
    relevant to this role.
    
    Return ONLY a valid JSON object with this structure:
    {{
        "question": "Your technical question here",
        "focus_area": "The technical area this question assesses",
        "difficulty": 4
    }}
    
    Difficulty scale: 1 (basic) to 5 (very challenging)
    Make the question specific and technical, not just theoretical.
    Do not include any explanation or markdown, just the JSON.
    """
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {tech_agent.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-4o",
                "messages": [{"role": "user", "content": tech_prompt}]
            }
        )
        
        response_text = response.json()["choices"][0]["message"]["content"]
        # Clean and parse the response (assuming clean_json_response is available)
        try:
            # Try to parse directly first
            question_data = json.loads(response_text.strip())
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group())
            else:
                raise json.JSONDecodeError("Could not extract JSON from response", response_text, 0)
        
        return {
            "question": question_data["question"],
            "interviewer_role": tech_agent.role.value,
            "focus_area": question_data.get("focus_area", "Technical"),
            "difficulty": question_data.get("difficulty", 4)
        }
    except Exception as e:
        print(f"Error generating tech question: {e}")
        # Fallback technical question
        tech_keyword = keywords[0] if keywords else "your technical skills"
        return {
            "question": f"Can you walk me through how you would approach solving a complex problem using {tech_keyword}? Please provide a specific example.",
            "interviewer_role": tech_agent.role.value,
            "focus_area": "Technical Problem Solving",
            "difficulty": 3
        }


def _select_agent_roles_for_job(target_job: str, num_agents: int) -> List[InterviewerRole]:
    """Select appropriate agent roles based on the job type"""
    job_lower = target_job.lower()

    # Prioritize agents based on job type
    if any(tech in job_lower for tech in ['engineer', 'developer', 'programmer', 'architect', 'technical']):
        priority_order = [
            InterviewerRole.TECHNICAL_LEAD,
            InterviewerRole.HIRING_MANAGER,
            InterviewerRole.SENIOR_PEER,
            InterviewerRole.HR_RECRUITER,
            InterviewerRole.INDUSTRY_EXPERT
        ]
    elif any(mgmt in job_lower for mgmt in ['manager', 'director', 'lead', 'head']):
        priority_order = [
            InterviewerRole.HIRING_MANAGER,
            InterviewerRole.HR_RECRUITER,
            InterviewerRole.INDUSTRY_EXPERT,
            InterviewerRole.SENIOR_PEER,
            InterviewerRole.TECHNICAL_LEAD
        ]
    elif any(design in job_lower for design in ['designer', 'ux', 'ui', 'creative']):
        priority_order = [
            InterviewerRole.HIRING_MANAGER,
            InterviewerRole.SENIOR_PEER,
            InterviewerRole.HR_RECRUITER,
            InterviewerRole.INDUSTRY_EXPERT,
            InterviewerRole.TECHNICAL_LEAD
        ]
    else:
        # Default order
        priority_order = [
            InterviewerRole.HIRING_MANAGER,
            InterviewerRole.HR_RECRUITER,
            InterviewerRole.SENIOR_PEER,
            InterviewerRole.INDUSTRY_EXPERT,
            InterviewerRole.TECHNICAL_LEAD
        ]

    return priority_order[:num_agents]


def _select_reviewing_roles(question_index: int) -> List[InterviewerRole]:
    """Select 2-3 agent roles to review each answer for diverse perspectives"""
    all_roles = list(InterviewerRole)

    # Rotate through roles to ensure variety
    # Use question index to deterministically select different reviewers
    start_idx = (question_index * 2) % len(all_roles)

    reviewing_roles = []
    num_reviewers = 2 if question_index < 2 else 3  # More reviewers for later questions

    for i in range(num_reviewers):
        idx = (start_idx + i) % len(all_roles)
        reviewing_roles.append(all_roles[idx])

    return reviewing_roles


def _synthesize_feedback(questions: List[str], answers: List[str],
                         all_feedback: List[List[Dict]], target_job: str,
                         keywords: List[str], api_key: str) -> Dict[str, Any]:
    """Synthesize feedback from multiple agents into cohesive feedback"""

    # Prepare structured feedback data
    structured_feedback = []
    for i, (question, answer) in enumerate(zip(questions, answers)):
        question_feedbacks = all_feedback[i]

        # Calculate average score and compile feedback
        avg_score = sum(f.get("score", 5) for f in question_feedbacks) / len(question_feedbacks)
        all_strengths = [s for f in question_feedbacks for s in f.get("strengths", [])]
        all_weaknesses = [w for f in question_feedbacks for w in f.get("weaknesses", [])]
        all_tips = [t for f in question_feedbacks for t in f.get("improvement_tips", [])]

        structured_feedback.append({
            "question": question,
            "answer": answer,
            "avg_score": avg_score,
            "strengths": list(set(all_strengths))[:3],  # Top 3 unique strengths
            "weaknesses": list(set(all_weaknesses))[:3],  # Top 3 unique weaknesses
            "tips": list(set(all_tips))[:3]  # Top 3 unique tips
        })

    # Use AI to synthesize into final feedback
    synthesis_prompt = f"""You are a senior interview coach synthesizing feedback from multiple interviewers.
    
    Job: {target_job}
    Skills: {', '.join(keywords)}
    
    Interview feedback from multiple reviewers:
    {json.dumps(structured_feedback, indent=2)}
    
    Create comprehensive, actionable feedback for each question and an overall summary.
    
    Return ONLY a valid JSON object:
    {{
        "question_feedback": [
            "Detailed, constructive feedback for question 1 that combines all reviewer perspectives",
            "Detailed, constructive feedback for question 2 that combines all reviewer perspectives", 
            "Detailed, constructive feedback for question 3 that combines all reviewer perspectives"
        ],
        "summary": "Overall assessment with specific, actionable advice for improvement. Include the candidate's key strengths and areas to focus on for this role."
    }}
    
    Make the feedback specific, balanced, and actionable. Do not include JSON formatting or markdown.
    """

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-4o",
                "messages": [{"role": "user", "content": synthesis_prompt}]
            }
        )

        response_text = response.json()["choices"][0]["message"]["content"]
        synthesized = json.loads(response_text)

        return synthesized

    except Exception as e:
        print(f"Error synthesizing feedback: {e}")
        # Fallback to simple concatenation
        return {
            "question_feedback": [
                f"For '{q['question']}': Strengths include {', '.join(q['strengths'][:2]) if q['strengths'] else 'good attempt'}. "
                f"Areas to improve: {', '.join(q['weaknesses'][:2]) if q['weaknesses'] else 'provide more specific examples'}. "
                f"Tips: {', '.join(q['tips'][:2]) if q['tips'] else 'practice similar questions'}."
                for q in structured_feedback
            ],
            "summary": f"Overall performance shows potential for the {target_job} role. "
                       f"Focus on demonstrating stronger expertise in {', '.join(keywords[:3])}. "
                       f"Practice providing specific examples from your experience.",
            "structured_feedback": structured_feedback
        }
