from flask import Flask, render_template, jsonify, request
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

STATE_FILE = Path(__file__).parent / "sync_state.json"
LOG_FILE = Path(__file__).parent / "sync.log"

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """Get current sync status."""
    state = {}
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    
    return jsonify({
        "last_sync": state.get("last_sync", {}),
        "now": datetime.now().isoformat(),
        "state_file_exists": STATE_FILE.exists()
    })

@app.route('/api/logs')
def api_logs():
    """Get recent log entries."""
    lines = []
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
    
    # Return last 100 lines
    return jsonify({
        "logs": lines[-100:] if lines else []
    })

@app.route('/api/sync', methods=['POST'])
def trigger_sync():
    """Trigger a sync run."""
    full_sync = request.json.get('full', False) if request.json else False
    
    try:
        # Run sync in background
        cmd = ['python3', 'sync.py']
        if full_sync:
            cmd.append('--full')
        
        # Start process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        return jsonify({
            "status": "started",
            "full_sync": full_sync,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/stats')
def api_stats():
    """Get sync statistics."""
    state = {}
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    
    stats = {
        "total_runs": state.get("total_runs", 0),
        "debtors_synced": state.get("debtors_synced", 0),
        "invoices_synced": state.get("invoices_synced", 0),
        "last_sync": state.get("last_sync", {})
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
