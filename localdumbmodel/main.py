# app.py
from fastapi import FastAPI, Request
from llama_cpp import Llama
import queue
import threading
import uuid
from typing import Dict
from pydantic import BaseModel
app = FastAPI()

# Replace with the actual path to your downloaded GGUF file
MODEL_PATH = "/home/sourav/Downloads/gemma-3-1b.gguf"

# Load the model (this happens once at startup)
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,  # Adjust context size as needed
    n_threads=4,  # Adjust based on your CPU cores
    verbose=False
)

# Queue for tasks
task_queue: queue.Queue = queue.Queue()

# Dictionary to store results (task_id -> response)
results: Dict[str, str] = {}

# Worker function to process inference tasks
def inference_worker():
    while True:
        task_id, prompt = task_queue.get()
        try:
            # Run inference
            response = llm(prompt, max_tokens=512, echo=False)["choices"][0]["text"]
            results[task_id] = response
        except Exception as e:
            results[task_id] = f"Error: {str(e)}"
        finally:
            task_queue.task_done()

# Start a single worker thread (llama-cpp-python is not fully thread-safe for concurrent inference on the same model instance;
# use multiple workers only if you load separate model instances or confirm thread safety for your setup)
worker_thread = threading.Thread(target=inference_worker, daemon=True)
worker_thread.start()

class GenerateRequest(BaseModel):
    prompt: str
    # You can easily add more fields later, e.g.:
    # max_tokens: int = 512
    # temperature: float = 0.7
    # stop: list[str] | None = None

@app.post("/generate")
async def generate(request: GenerateRequest):
    """
    Accepts a prompt and queues it for processing.
    Returns a task_id immediately (non-blocking).
    """
    task_id = str(uuid.uuid4())
    task_queue.put((task_id, request.prompt))
    return {"task_id": task_id, "status": "queued"}
@app.get("/result/{task_id}")
def get_result(task_id: str):
    """
    Polls for the result of a queued task.
    """
    if task_id in results:
        response = results.pop(task_id)
        return {"status": "completed", "response": response}
    else:
        return {"status": "processing"}
