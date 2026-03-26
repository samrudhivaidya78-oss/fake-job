import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Enable CORS so the frontend can communicate with the backend
CORS(app)

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Warning: Missing SUPABASE_URL or SUPABASE_KEY. DB insertions will fail.")
    supabase = None
else:
    try:
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        supabase = None

SCAM_KEYWORDS = [
    "easy money",
    "no experience",
    "urgent hiring",
    "immediate joining",
    "payment required",
    "wire transfer",
    "data entry",
    "processing fee",
    "guaranteed income",
    "work from home",
    "female candidates",
    "whatsapp to",
    "bank details"
]

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Empty input provided"}), 400
    
    text = data.get('text', '')
    if not text.strip():
        return jsonify({"error": "Job description cannot be empty"}), 400

    text_lower = text.lower()
    
    flagged_keywords = []
    for keyword in SCAM_KEYWORDS:
        if keyword in text_lower:
            flagged_keywords.append(keyword)
             
    # Calculate Risk Score
    # 0 keywords = 10% base risk
    # Each keyword adds 20-30%
    risk_score = 10 + (len(flagged_keywords) * 20)
    
    # Cap at 100
    if risk_score > 100:
        risk_score = 100
    
    if len(flagged_keywords) == 0:
        risk_score = 5 # Very low risk if nothing is flagged
    
    # Determine risk level based on score
    if risk_score < 30:
        risk_level = "low"
    elif risk_score < 60:
        risk_level = "medium"
    else:
        risk_level = "high"
        
    classification = "Fake" if risk_score > 50 else "Genuine"
    
    # Supabase insertion
    if supabase:
        try:
            supabase.table("job_scans").insert({
                "job_text": text,
                "result": classification,
                "risk_score": risk_score,
                "flagged_keywords": flagged_keywords
            }).execute()
        except Exception as e:
            print(f"Error inserting into Supabase: {e}")

    return jsonify({
        "risk_score": risk_score,
        "risk_level": risk_level,
        "classification": classification,
        "flagged_keywords": flagged_keywords
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
