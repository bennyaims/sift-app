from langchain_ollama import ChatOllama
from pydantic import BaseModel
from typing import List, Dict
import json

llm = ChatOllama(
    model="labour-hire-expert",
    temperature=0.3,
    num_ctx=32768
)

class WorkerProfile(BaseModel):
    name: str
    skills: List[str]
    location: str
    experience_years: int
    availability: str
    pay_expectation: float

class Job(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    location: str
    pay_rate: float
    shift_date: str

def match_workers_to_job(job: Job, workers: List[WorkerProfile]) -> List[Dict]:
    results = []
    
    for worker in workers:
        prompt = f"""
Rate how well this worker matches the job (0-100).

JOB:
Title: {job.title}
Location: {job.location}
Pay: ${job.pay_rate}/hr
Required Skills: {job.required_skills}
Date: {job.shift_date}
Description: {job.description}

WORKER:
Name: {worker.name}
Location: {worker.location}
Skills: {worker.skills}
Experience: {worker.experience_years} years
Availability: {worker.availability}
Expected Pay: ${worker.pay_expectation}/hr

Return ONLY valid JSON:
{{"score": 85, "reasoning": "short explanation", "strengths": ["list"], "weaknesses": ["list"]}}
"""

        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            match = json.loads(content)
            
            results.append({
                "worker_name": worker.name,
                "score": int(match.get("score", 50)),
                "reasoning": match.get("reasoning", ""),
                "strengths": match.get("strengths", []),
                "weaknesses": match.get("weaknesses", [])
            })
        except:
            results.append({
                "worker_name": worker.name,
                "score": 50,
                "reasoning": "Could not process match",
                "strengths": [],
                "weaknesses": []
            })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
