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
from django.conf import settings
from interview.models import InterviewSession
from jobify_backend.logger import logger
from jobify_backend.settings import MAX_VIDEO_FILE_SIZE
from rest_framework.response import Response


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
            logger.error(f"Error generating question for {self.role.value}: {e}")
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
            logger.error(f"Error evaluating answer for {self.role.value}: {e}")
            return {
                "score": 5,
                "strengths": ["Attempted to answer"],
                "weaknesses": ["Could not evaluate properly"],
                "specific_feedback": "Error in evaluation",
                "improvement_tips": ["Try to provide more specific examples"]
            }

def clean_json_response(response_text):
    """Clean markdown formatting from JSON responses"""
    # Remove leading/trailing whitespace
    cleaned = response_text.strip()

    # This finds the first { and last } to extract just the JSON object
    json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{[^{}]*\}', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group()
    
    return cleaned