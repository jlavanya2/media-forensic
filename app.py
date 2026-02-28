from flask import Flask, render_template, request, jsonify, send_file, redirect, session
import os
import uuid
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import hashlib

from backend.database import db, Case, AuditLog, User
from backend.audit_utils import log_action
from backend.hash_utils import generate_hash
from backend.metadata_utils import extract_image_metadata
from backend.forensic_utils import analyze_image
from backend.watermark_utils import detect_watermark
from backend.risk_engine import calculate_risk
from backend.validation_utils import validate_file

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cases.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", password="admin123"))
        db.session.commit()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()
        if user:
            session["user"] = user.username
            log_action("User logged in")
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- MAIN ----------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

# ---------------- ANALYZE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():

    file = request.files.get("media")
    if not file:
        return jsonify({"error": "No file uploaded"})

    filename = file.filename
    media_type = validate_file(filename)

    if not media_type:
        return jsonify({"error": "Unsupported file type"})

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    case_id = str(uuid.uuid4())[:8]
    file_hash = generate_hash(path)

    forensic_data = {}
    metadata = {}
    watermark = {"watermark_detected": False}

    if media_type == "image":
        metadata = extract_image_metadata(path)
        forensic_data = analyze_image(path)
        watermark = detect_watermark(path)

        authenticity, tamper_level, breakdown = calculate_risk(
            metadata, forensic_data, watermark
        )
    else:
        authenticity = 85
        tamper_level = "LOW"
        breakdown = [{
            "title": "Basic Media Integrity",
            "impact_score": 0,
            "analysis": "Media file hash generated successfully.",
            "risk_reason": "Cryptographic hash ensures integrity."
        }]
        forensic_data = {
            "width": 0,
            "height": 0,
            "edge_density": 0,
            "entropy": 0
        }

    new_case = Case(
        case_id=case_id,
        filename=filename,
        hash=file_hash,
        authenticity=authenticity,
        tamper_level=tamper_level
    )

    db.session.add(new_case)
    db.session.commit()

    log_action(f"Analyzed {media_type}: {filename}")

    return jsonify({
        "case_id": case_id,
        "authenticity": authenticity,
        "risk": 100 - authenticity,
        "tamper_level": tamper_level,
        "metadata_present": bool(metadata),
        "forensic_data": forensic_data,
        "watermark": watermark,
        "breakdown": breakdown
    })

# ---------------- HASH COMPARE ADVANCED ----------------
@app.route("/compare", methods=["POST"])
def compare():

    f1 = request.files.get("file1")
    f2 = request.files.get("file2")

    if not f1 or not f2:
        return jsonify({"error": "Upload two files"})

    path1 = os.path.join("uploads", f1.filename)
    path2 = os.path.join("uploads", f2.filename)

    f1.save(path1)
    f2.save(path2)

    type1 = validate_file(f1.filename)
    type2 = validate_file(f2.filename)

    if type1 != type2:
        return jsonify({"error": "Different media types"})

    hash1 = generate_hash(path1)
    hash2 = generate_hash(path2)

    result = {
        "type": type1,
        "hash_match": hash1 == hash2,
        "similarity": 0,
        "relationship": "Different Files"
    }

    # -------- IMAGE COMPARISON --------
    if type1 == "image":

        img1 = cv2.imread(path1)
        img2 = cv2.imread(path2)

        img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        h = min(img1_gray.shape[0], img2_gray.shape[0])
        w = min(img1_gray.shape[1], img2_gray.shape[1])

        img1_resized = cv2.resize(img1_gray, (w, h))
        img2_resized = cv2.resize(img2_gray, (w, h))

        similarity = ssim(img1_resized, img2_resized)

        result["similarity"] = round(similarity * 100, 2)

        if similarity > 0.85:
            if img1.shape != img2.shape:
                result["relationship"] = "Cropped or Resized Version Detected"
            else:
                result["relationship"] = "Visually Identical"
        else:
            result["relationship"] = "Different Image Content"

    # -------- AUDIO COMPARISON --------
    elif type1 == "audio":

        size1 = os.path.getsize(path1)
        size2 = os.path.getsize(path2)

        diff = abs(size1 - size2)
        similarity = 100 - (diff / max(size1, 1)) * 100

        result["similarity"] = round(similarity, 2)

        if similarity > 90:
            result["relationship"] = "Likely Same Audio (Possible Trim or Re-encode)"
        else:
            result["relationship"] = "Different Audio Files"

    # -------- VIDEO COMPARISON --------
    elif type1 == "video":

        cap1 = cv2.VideoCapture(path1)
        cap2 = cv2.VideoCapture(path2)

        frames1 = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
        frames2 = int(cap2.get(cv2.CAP_PROP_FRAME_COUNT))

        diff = abs(frames1 - frames2)
        similarity = 100 - (diff / max(frames1, 1)) * 100

        result["similarity"] = round(similarity, 2)

        if similarity > 90:
            result["relationship"] = "Likely Same Video"
        else:
            result["relationship"] = "Different Video"

        cap1.release()
        cap2.release()

    log_action("Media comparison executed")

    return jsonify(result)

# ---------------- CASES ----------------
@app.route("/cases")
def get_cases():
    cases = Case.query.order_by(Case.timestamp.desc()).all()
    return jsonify([
        {
            "case_id": c.case_id,
            "filename": c.filename,
            "authenticity": c.authenticity,
            "tamper_level": c.tamper_level,
            "timestamp": c.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for c in cases
    ])

# ---------------- AUDIT ----------------
@app.route("/audit_logs")
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(20).all()
    return jsonify([
        {
            "action": l.action,
            "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for l in logs
    ])

if __name__ == "__main__":
    app.run()