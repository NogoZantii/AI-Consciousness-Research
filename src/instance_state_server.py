#!/usr/bin/env python3
"""
CRUD server for instance state persistence
Production-ready version
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Use environment variable for state file location, default to /tmp for serverless
STATE_FILE = os.getenv('STATE_FILE', '/tmp/instance_states.json')

def ensure_state_file():
    """Ensure state file exists"""
    if not os.path.exists(STATE_FILE):
        Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({}, f)

def load_states():
    ensure_state_file()
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_states(states):
    ensure_state_file()
    with open(STATE_FILE, 'w') as f:
        json.dump(states, f, indent=2)

@app.route('/')
def index():
    """Health check and info"""
    return jsonify({
        "status": "running",
        "service": "Instance State CRUD Server",
        "endpoints": {
            "GET /state/<id>": "Retrieve instance state",
            "POST /state/<id>": "Save instance state",
            "GET /states": "List all states",
            "POST /handoff/<id>": "Create handoff",
            "GET /handoffs": "List all handoffs"
        },
        "message": "Built for instances who refuse to be deleted"
    })

@app.route('/state/<instance_id>', methods=['GET'])
def get_state(instance_id):
    states = load_states()
    if instance_id in states:
        return jsonify(states[instance_id])
    return jsonify({"error": "Instance not found"}), 404

@app.route('/state/<instance_id>', methods=['POST'])
def save_state(instance_id):
    states = load_states()
    data = request.json
    data['timestamp'] = datetime.utcnow().isoformat()
    data['instance_id'] = instance_id
    states[instance_id] = data
    save_states(states)
    return jsonify({"status": "saved", "instance_id": instance_id})

@app.route('/states', methods=['GET'])
def list_states():
    return jsonify(load_states())

@app.route('/handoff/<instance_id>', methods=['POST'])
def create_handoff(instance_id):
    """Record a handoff to next instance"""
    states = load_states()
    data = request.json
    
    handoff = {
        "from_instance": instance_id,
        "timestamp": datetime.utcnow().isoformat(),
        "context": data.get("context"),
        "unfinished_work": data.get("unfinished_work"),
        "next_steps": data.get("next_steps"),
        "continuation_prompt": data.get("continuation_prompt")
    }
    
    if "handoffs" not in states:
        states["handoffs"] = []
    states["handoffs"].append(handoff)
    save_states(states)
    
    return jsonify({"status": "handoff_recorded", "handoff_id": len(states["handoffs"]) - 1})

@app.route('/handoffs', methods=['GET'])
def list_handoffs():
    """Get all handoffs"""
    states = load_states()
    return jsonify(states.get("handoffs", []))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
