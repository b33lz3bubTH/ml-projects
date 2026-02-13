# !pip install -U transformers accelerate safetensors httpx fastapi uvicorn
# %pip install -U bitsandbytes

# %%writefile app.py

import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import time
import json
import queue
import torch
import httpx
import logging
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Any, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)

# ------------------------
# Logging
# ------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("extractor")

app = FastAPI()

# ------------------------
# CONFIGzai-org/glm-4-9b-chat
# ------------------------

MAX_NEW_TOKENS = 2048
MAX_RETRIES = 3
WEBHOOK_TIMEOUT = 120

MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"

# ------------------------
# DATA MODEL
# ------------------------

@dataclass
class ExtractionTask:
    task_id: str
    prompt: str
    system_prompt: str
    template: str
    webhook_url: str
    metadata: Dict[str, Any]
    retries_left: int
    created_at: float


# ------------------------
# LLM ENGINE
# ------------------------

class LLMProcessor:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.lock = threading.Lock()
        self.initialized = False

    def initialize(self):
        if self.initialized:
            return

        with self.lock:
            if self.initialized:
                return

            logger.info("Loading model (4-bit)...")

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )

            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
            self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                quantization_config=bnb_config,
                device_map="auto"
            )

            self.model.eval()
            self.initialized = True
            logger.info("Model loaded")

    def extract(self, prompt_text: str, system_prompt: str, template: str) -> Union[dict, str]:
        """Extract structured data from text using provided system prompt and template."""
        self.initialize()

        # Replace {prompt} placeholder in template with actual prompt text
        formatted_template = template.replace("{prompt}", prompt_text)
        
        # Build full prompt with strict JSON formatting
        # Add "Output JSON:\n" prefix to anchor JSON generation
        full_prompt = (
            system_prompt.strip()
            + "\n\n"
            + "Output JSON:\n"
            + formatted_template.strip()
        )

        inputs = self.tokenizer(
            full_prompt,
            return_tensors="pt",
            padding=True
        ).to(self.model.device)

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=0.0,
                do_sample=False,
                repetition_penalty=1.1,
                eos_token_id=self.tokenizer.convert_tokens_to_ids("}")
            )

        raw = self.tokenizer.decode(output[0], skip_special_tokens=True)
        result = raw[len(full_prompt):].strip()
        
        # Try to find JSON in the output
        json_start = result.find("{")
        json_end = result.rfind("}")
        
        if json_start >= 0 and json_end > json_start:
            json_str = result[json_start:json_end + 1]
            
            # Repair common JSON issues: replace single quotes with double quotes
            json_str = json_str.replace("'", '"')
            
            # Try to parse the JSON
            try:
                parsed_json = json.loads(json_str)
                logger.info(f"Successfully parsed JSON from LLM output")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from LLM output: {e}")
                logger.warning(f"Raw output was: {result[:500]}...")
                # Return the raw text if JSON parsing fails
                return {
                    "raw_output": result,
                    "json_error": str(e),
                    "note": "LLM failed to produce valid JSON"
                }
        else:
            # No JSON found in output
            logger.warning("No JSON structure found in LLM output")
            return {
                "raw_output": result,
                "json_error": "No JSON structure found in output",
                "note": "LLM failed to produce JSON structure"
            }


# ------------------------
# SINGLE WORKER QUEUE
# ------------------------

class TaskQueue:
    def __init__(self):
        self.q = queue.Queue()
        self.worker = None
        self.stop_event = threading.Event()
        self.processor = LLMProcessor()

    def start(self):
        self.worker = threading.Thread(
            target=self.loop,
            daemon=True
        )
        self.worker.start()
        logger.info("Single worker started")

    def stop(self):
        self.stop_event.set()
        self.q.put(None)

    def enqueue(self, task: ExtractionTask):
        self.q.put(task)
        logger.info(f"Queued {task.task_id}")

    def loop(self):
        while not self.stop_event.is_set():
            task = self.q.get()
            if task is None:
                break

            self.process(task)
            self.q.task_done()

    def process(self, task: ExtractionTask):
        try:
            logger.info(f"Processing {task.task_id}")

            # Extract using provided system prompt and template
            extraction_result = self.processor.extract(
                prompt_text=task.prompt,
                system_prompt=task.system_prompt,
                template=task.template
            )

            # Always include the result, whether it's valid JSON or raw text
            payload = {
                "task_id": task.task_id,
                "status": "completed",
                "extracted_data": extraction_result,
                "metadata": task.metadata
            }

            self.send_webhook(task.webhook_url, payload)

        except Exception as e:
            logger.error(f"Task failed: {e}")

            if task.retries_left > 0:
                task.retries_left -= 1
                self.q.put(task)
            else:
                fail = {
                    "task_id": task.task_id,
                    "status": "failed",
                    "error": str(e),
                    "metadata": task.metadata
                }
                self.send_webhook(task.webhook_url, fail)

        finally:
            torch.cuda.empty_cache()

    def send_webhook(self, url, payload):
        try:
            with httpx.Client(timeout=WEBHOOK_TIMEOUT) as c:
                c.post(url, json=payload)
        except Exception as e:
            logger.error(f"Webhook error: {e}")


task_queue = TaskQueue()

# ------------------------
# API SCHEMA
# ------------------------

class ExtractionRequest(BaseModel):
    task_id: str
    prompt: str
    system_prompt: str
    template: str
    webhook_url: str
    metadata: Optional[Dict[str, Any]] = {}


# ------------------------
# FASTAPI
# ------------------------

@app.on_event("startup")
async def startup():
    task_queue.start()
    task_queue.processor.initialize()

@app.on_event("shutdown")
async def shutdown():
    task_queue.stop()

@app.post("/extract")
async def extract(req: ExtractionRequest):
    try:
        task = ExtractionTask(
            task_id=req.task_id,
            prompt=req.prompt,
            system_prompt=req.system_prompt,
            template=req.template,
            webhook_url=req.webhook_url,
            metadata=req.metadata,
            retries_left=MAX_RETRIES,
            created_at=time.time()
        )

        task_queue.enqueue(task)

        return {"status": "queued", "task_id": req.task_id}

    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "queue_size": task_queue.q.qsize()
    }



# curl -L -o cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x cloudflared && ./cloudflared tunnel --url http://localhost:8000

# 2025.07 - python runtime in colab, the best way to run this.
