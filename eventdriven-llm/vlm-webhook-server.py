#!/usr/bin/env python3
"""
Simple webhook listener to receive VLM extraction results
"""

from flask import Flask, request, jsonify
import argparse
import logging
import json

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook-listener")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive webhook from VLM extractor"""
    try:
        payload = request.json
        logger.info("📨 Received webhook:")
        logger.info(f"   Task ID: {payload.get('task_id')}")
        logger.info(f"   Status: {payload.get('status')}")
        
        if payload.get('status') == 'completed':
            extracted_data = payload.get('extracted_data', {})
            logger.info(f"   Extracted Data: {jsonify(extracted_data).get_data(as_text=True)}")
        else:
            logger.info(f"   Error: {payload.get('error')}")
        
        # You can save results to file here
        with open(f"results_{payload.get('task_id')}.json", 'w') as f:
            json.dump(payload, f, indent=2)
        
        return jsonify({"status": "received"}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "listener": "active"})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Webhook Listener")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    args = parser.parse_args()
    
    print(f"🚀 Webhook listener running on http://localhost:{args.port}/webhook")
    print(f"📝 Results will be saved to results_<task_id>.json files")
    app.run(host='0.0.0.0', port=args.port, debug=True)
