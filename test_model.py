from langchain_ollama import ChatOllama
import time

print("Connecting to Labour Hire Expert...\n")

llm = ChatOllama(
    model="labour-hire-expert",
    temperature=0.3,
    num_ctx=32768
)

test_prompt = """
Match this worker to suitable jobs in Melbourne:

Worker: 
- Name: John Smith
- Skills: Forklift ticket, RF scanner, 5 years warehouse experience
- Location: Dandenong, VIC
- Availability: This weekend (Sat & Sun)
- Pay expectation: $32+/hr
"""

print("Sending test to model...\n")
start = time.time()
response = llm.invoke(test_prompt)
end = time.time()

print(response.content)
print(f"\nTime taken: {end-start:.1f} seconds")
