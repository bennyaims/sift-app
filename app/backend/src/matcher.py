from langchain_ollama import ChatOllama, OllamaEmbeddings
from  pydantic import BaseModel
from typing import List

llm = ChatOllama(
    model="labour-hire-expert",
    temperature=0.3,
    num_ctx=32768
)

embeddings = OllamaEmbeddings(model="nomic-embed-text")

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

def match_worker_to_job(worker: WorkerProfile, job: Job):
    prompt = f"""
    Score how well this worker matches the job (0-100).
    Consider skills match, location, experience, availability and pay.

    Worker: {worker}
    Job: {job}

    Return only a JSON with:
    {{"score": number, "reasoning": "short explanation", "strengths": [], "concerns": []}}
    """

    response = llm.invoke(prompt)
    print(response.content)   # We'll improve this to parse JSON later
    return response.content
