# TODO - Daemonology RAG API Issues & Notes

## Configuration Required
- [ ] Set API keys in `.env` file:
  - **For LLM (OpenRouter)**: Set `OPENROUTER_API_KEY` and `LLM_MODEL` (e.g., `openai/gpt-3.5-turbo`, `anthropic/claude-3-haiku`, etc.)
  - **For Embeddings (OpenAI)**: Set `OPENAI_API_KEY` (required for embeddings)
  - Example: 
    ```
    OPENROUTER_API_KEY=your_openrouter_key
    LLM_MODEL=openai/gpt-3.5-turbo
    OPENAI_API_KEY=your_openai_key
    ```

## Testing Status
- ✅ Docker build successful
- ✅ Containers start successfully
- ✅ Health endpoint working (`GET /health`)
- ✅ Database initialization working (pgvector extension enabled)
- ✅ Hot reload working (code changes auto-reload)
- ⚠️ Query endpoint requires valid OPENAI_API_KEY to function
- ⚠️ Upload endpoint requires valid OPENAI_API_KEY to function

## Implementation Notes
- All core functionality implemented according to SRS
- LLM configuration supports OpenRouter (with model selection) and OpenAI
- OpenRouter integration: Uses OpenAI-compatible API with custom base URL
- Error handling in place
- Logging configured

