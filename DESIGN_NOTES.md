# Design Notes

A few thoughts on the architecture and what I'd change if this were a real production system.

### 1. Validation vs Routing
Right now, the boundary between "bad request" (HTTP 422) and "bad document" (HITL routing) is a little fuzzy. 

I split it up so that missing `shipment_id` returns a 422 (because the system literally can't process it), but low confidence scores return a 200 with a `hitl_review` route. In a real system, I'd want a proper chain-of-responsibility pattern for the validators. Some rules throw hard errors, others just flag the envelope for manual review. Hardcoding the rules in a massive `validate()` function won't scale once we have 50 different clients with different date rules.

### 2. Mutating the Envelope
The `run_matching` service mutates the envelope object passed into it. It's convenient for a small prototype like this, but passing mutable state through a pipeline is usually a recipe for subtle bugs. 

If I had more time, I'd change the services to be pure functions that return a `MatchResult` or `ValidationResult` object, and let the API layer (or a proper workflow engine) attach them to the envelope.

### 3. The LLM Client
I used `httpx` directly for the Groq calls to keep dependencies light, but obviously in prod we'd probably want to use the official SDKs or LangChain/LiteLLM if we needed to support multiple providers easily. The retry/timeout logic is also pretty basic right now.
