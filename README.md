# Document Intelligence Platform (Interview Task)

This is a doc intelligence pipeline. It takes JSON Execution Envelopes as input and runs them through a validation and matching pipeline.

## Getting started

It's just a standard FastAPI app.

```bash
pip install -r requirements.txt
cp .env.example .env   # don't forget to add your Groq API key here!
uvicorn app.main:app --reload
```

Or just use Docker if you don't want to mess with python envs:

```bash
docker build -t doc-intel .
docker run -p 8000:8000 --env-file .env doc-intel
```

## What's in here

I've implemented all three parts of the task:

1. **Validation (`/validate`)**: Checks the envelope for required fields (returns 422 if they're missing). Then it validates confidence scores and ship dates against the threshold in the envelope. Routes are decided here (auto_approve, hitl_review, rejected).
2. **Matching (`/match`)**: If the commodity code confidence is trash, we hit Groq (Llama 3.3 70B) to try and match the description against our reference catalog.
3. **Pipeline (`/process`)**: Wires it all together. 

Tests cover all the edge cases (15 passing tests right now). 

```bash
pytest
```
*Note: The tests mock the LLM calls using a dependency override, so you don't need a Groq key just to run the test suite.*

## Structure

- `app/api/` - FastAPI routers
- `app/services/` - The actual business logic (validation rules, LLM prompting).
- `app/models/` - Pydantic schemas. The envelope structure is defined here.

## Swapping the LLM

If you want to run the app without Groq, open up `app/services/matching_service.py` and change `get_client()` to return `MockLLMClient()` instead of `GroqClient()`. The mock just does some keyword matching but it's enough to test the flow.
