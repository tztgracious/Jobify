import json
import os
import json
import re
import requests
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import random
import requests
from deepgram import DeepgramClient, PrerecordedOptions
from django.conf import settings
from interview.models import InterviewSession
from jobify_backend.logger import logger
from jobify_backend.settings import MAX_VIDEO_FILE_SIZE
from rest_framework.response import Response


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

def clean_json_response(response_text):
    """Clean markdown formatting from JSON responses"""
    
    # Remove leading/trailing whitespace
    cleaned = response_text.strip()
    
    # Method 1: Remove markdown code blocks
    if cleaned.startswith("```json"):
        # Remove opening ```json
        cleaned = cleaned[7:]
        # Remove closing ```
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    elif cleaned.startswith("```"):
        # Remove generic code blocks
        cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    
    # Method 2: Extract JSON using regex (more robust)
    # This finds the first { and last } to extract just the JSON object
    json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{[^{}]*\}', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group()
    
    return cleaned

class InterviewerRole(Enum):
    HR_RECRUITER = "HR Recruiter"
    TECHNICAL_LEAD = "Technical Lead"
    HIRING_MANAGER = "Hiring Manager"
    INDUSTRY_EXPERT = "Industry Expert"
    SENIOR_PEER = "Senior Peer"


class BaseAgent:
    """Base class for all interview agents"""
    
    def __init__(self, role: InterviewerRole, api_key: str):
        self.role = role
        self.api_key = api_key
        self.personality = self._define_personality()
    
    def _define_personality(self) -> str:
        """Define the personality and focus for each agent type"""
        personalities = {
            InterviewerRole.HR_RECRUITER: """You are an experienced HR recruiter who focuses on:
                - Cultural fit and company values alignment
                - Communication skills and interpersonal abilities
                - Career motivation and growth mindset
                - Conflict resolution and teamwork
                - Work-life balance and expectations""",
            
            InterviewerRole.TECHNICAL_LEAD: """You are a senior technical lead who evaluates:
                - Technical proficiency and coding skills
                - System design and architecture understanding
                - Problem-solving approach and analytical thinking
                - Knowledge of best practices and design patterns
                - Ability to explain complex technical concepts""",
            
            InterviewerRole.HIRING_MANAGER: """You are a hiring manager who assesses:
                - Practical experience and project management
                - Business acumen and strategic thinking
                - Leadership potential and initiative
                - Ability to deliver results and meet deadlines
                - Cross-functional collaboration skills""",
            
            InterviewerRole.INDUSTRY_EXPERT: """You are an industry expert who examines:
                - Current industry trends and technologies
                - Competitive landscape knowledge
                - Innovation and adaptability
                - Domain-specific expertise
                - Understanding of market challenges""",
            
            InterviewerRole.SENIOR_PEER: """You are a senior peer who explores:
                - Technical collaboration and mentoring abilities
                - Code review and feedback skills
                - Team dynamics and communication
                - Knowledge sharing and documentation
                - Day-to-day work scenarios"""
        }
        return personalities.get(self.role, "You are a professional interviewer.")
    
    def generate_question_sync(self, target_job: str, keywords: List[str]) -> Dict[str, Any]:
        """Synchronous version of question generation"""
        prompt = f"""{self.personality}
        
        You're interviewing for: {target_job}
        Key skills/keywords: {', '.join(keywords)}
        
        Generate ONE realistic interview question that you would ask in a real interview.
        The question should be specific to your role as {self.role.value} and your focus areas.
        
        Return ONLY a valid JSON object with this structure:
        {{
            "question": "Your question here",
            "focus_area": "The main skill or area this question assesses",
            "difficulty": 3
        }}
        
        Difficulty scale: 1 (basic) to 5 (very challenging)
        Make the question practical and scenario-based when possible.
        Do not include any explanation or markdown, just the JSON.
        """
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            response_text = response.json()["choices"][0]["message"]["content"]
            # Clean and parse the response
            cleaned_text = clean_json_response(response_text)
            question_data = json.loads(cleaned_text)
            
            return {
                "question": question_data["question"],
                "interviewer_role": self.role.value,
                "focus_area": question_data.get("focus_area", "General"),
                "difficulty": question_data.get("difficulty", 3)
            }
        except Exception as e:
            print(f"Error generating question for {self.role.value}: {e}")
            print(response_text)
            return {
                "question": f"Tell me about your experience with {keywords[0] if keywords else 'this role'}.",
                "interviewer_role": self.role.value,
                "focus_area": "General Experience",
                "difficulty": 2
            }
    
    def evaluate_answer_sync(self, question: str, answer: str, target_job: str, keywords: List[str]) -> Dict[str, Any]:
        """Synchronous version of answer evaluation"""
        prompt = f"""{self.personality}
        
        Job: {target_job}
        Required skills: {', '.join(keywords)}
        
        Question asked: "{question}"
        Candidate's answer: "{answer}"
        
        Evaluate this answer from your specific perspective as a {self.role.value}.
        
        Return ONLY a valid JSON object:
        {{
            "score": 7,
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"],
            "specific_feedback": "Detailed feedback from your role's perspective",
            "improvement_tips": ["tip1", "tip2"]
        }}
        
        Score should be out of 10. Do not include any explanation or markdown, just the JSON.
        """
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                        
                }
            )
            response_text = response.json()["choices"][0]["message"]["content"]
            cleaned_text = clean_json_response(response_text)
            return json.loads(cleaned_text)
        except Exception as e:
            print(f"Error evaluating answer for {self.role.value}: {e}")
            print(response_text)
            return {
                "score": 5,
                "strengths": ["Attempted to answer"],
                "weaknesses": ["Could not evaluate properly"],
                "specific_feedback": "Error in evaluation",
                "improvement_tips": ["Try to provide more specific examples"]
            }


def get_questions_using_openai_multi_agent(target_job, keywords):
    """Multi-agent version that maintains the same interface as the original function"""
    api_key = os.getenv('OPEN_ROUTER_API_KEY')
    
    # Select which agents to use based on the job type
    selected_roles = _select_agent_roles_for_job(target_job, num_agents=3)
    
    # Create agents
    agents = [BaseAgent(role, api_key) for role in selected_roles]
    
    # Generate questions from each agent
    questions_data = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(agent.generate_question_sync, target_job, keywords)
            for agent in agents
        ]
        
        for future in futures:
            question_data = future.result()
            questions_data.append(question_data)
    
    # Sort by difficulty for better flow
    questions_data.sort(key=lambda q: q.get("difficulty", 3))
    
    # Return just the question texts to maintain compatibility
    return [q["question"] for q in questions_data]


def get_feedback_using_openai_multi_agent(resume, interview_session):
    """Multi-agent version that maintains the same interface as the original function"""
    api_key = os.getenv('OPEN_ROUTER_API_KEY')
    
    questions = interview_session.questions
    answers = interview_session.answers
    target_job = resume.target_job
    keywords = resume.keywords
    
    # Get feedback from multiple agents
    all_feedback = []
    
    # For each question, get feedback from 2-3 different agents
    for i, (question, answer) in enumerate(zip(questions, answers)):
        # Select different agents for each question to get diverse perspectives
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
        
        all_feedback.append(question_feedback)
    
    # Synthesize feedback from all agents
    synthesized_feedback = _synthesize_feedback(questions, answers, all_feedback, target_job, keywords, api_key)
    
    # Format to match expected output
    formatted_feedback = {
        "question_1_feedback": synthesized_feedback["question_feedback"][0],
        "question_2_feedback": synthesized_feedback["question_feedback"][1],
        "question_3_feedback": synthesized_feedback["question_feedback"][2],
        "summary": synthesized_feedback["summary"],
        
    }
    
    return formatted_feedback


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
            "structured_feedback":structured_feedback
        }