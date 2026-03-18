"""
Healthcare AI Diagnostic System — Flask Application
Endpoints:
  GET  /           → Dashboard
  GET  /login      → Login page
  POST /login      → Authenticate
  GET  /logout     → Logout
  GET  /diagnose   → Diagnosis form selector
  GET  /diagnose/symptoms  → Symptom checker form
  POST /diagnose/symptoms  → Run symptom inference
  GET  /diagnose/heart     → Heart disease form
  POST /diagnose/heart     → Run heart disease inference
  GET  /metrics            → Model performance dashboard
  GET  /history            → Session prediction history
"""
import os, json, sys
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)

# Ensure project root on path
sys.path.insert(0, os.path.dirname(__file__))

from utils.security import (
    verify_user, login_required, rate_limit,
    log_audit_event, sanitize_float, sanitize_int, sanitize_symptoms
)
from model.predict import (
    predict_heart_disease, predict_symptom_disease,
    get_all_symptoms, get_model_metrics
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production-32bytes")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB

# ── In-session prediction history ────────────────────────────────────
def _get_history():
    return session.get("history", [])

def _add_history(entry: dict):
    hist = _get_history()
    hist.insert(0, entry)
    session["history"] = hist[:20]   # keep last 20


# ─────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if verify_user(username, password):
            session.clear()
            session["logged_in"]  = True
            session["username"]   = username
            session["login_time"] = datetime.utcnow().isoformat()
            return redirect(url_for("dashboard"))
        flash("Invalid credentials. Please try again.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    user = session.get("username", "unknown")
    log_audit_event("LOGOUT", user)
    session.clear()
    return redirect(url_for("login"))


# ─────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def dashboard():
    metrics  = get_model_metrics()
    history  = _get_history()
    username = session.get("username", "user")
    return render_template("index.html",
                           metrics=metrics,
                           history=history,
                           username=username)


# ─────────────────────────────────────────────────────────────────────
# SYMPTOM CHECKER
# ─────────────────────────────────────────────────────────────────────
@app.route("/diagnose/symptoms", methods=["GET", "POST"])
@login_required
@rate_limit
def symptom_diagnose():
    all_symptoms = get_all_symptoms()
    if request.method == "POST":
        raw_symptoms = request.form.getlist("symptoms")
        age    = sanitize_int(request.form.get("age", 40), 1, 120, 40)
        gender = request.form.get("gender", "Unknown")
        gender = gender if gender in ("Male", "Female", "Other") else "Unknown"
        note   = request.form.get("note", "").strip()[:500]

        # Whitelist validation
        valid_symptoms = sanitize_symptoms(raw_symptoms, all_symptoms)
        if not valid_symptoms:
            flash("Please select at least one symptom.", "warning")
            return render_template("symptom_form.html", symptoms=all_symptoms)

        result = predict_symptom_disease(valid_symptoms, age, gender)
        result["patient_age"]    = age
        result["patient_gender"] = gender
        result["note"]           = note
        result["timestamp"]      = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        log_audit_event("SYMPTOM_PREDICTION", session.get("username"),
                        {"num_symptoms": len(valid_symptoms),
                         "primary": result["primary_diagnosis"]})

        _add_history({
            "type": "Symptom Check",
            "diagnosis": result["primary_diagnosis"],
            "probability": result["probability"],
            "timestamp": result["timestamp"],
        })

        return render_template("results.html", result=result, mode="symptom")

    return render_template("symptom_form.html", symptoms=all_symptoms)


# ─────────────────────────────────────────────────────────────────────
# HEART DISEASE PREDICTOR
# ─────────────────────────────────────────────────────────────────────
@app.route("/diagnose/heart", methods=["GET", "POST"])
@login_required
@rate_limit
def heart_diagnose():
    if request.method == "POST":
        form = {
            "age":      sanitize_int(request.form.get("age"), 1, 120, 50),
            "sex":      sanitize_int(request.form.get("sex"), 0, 1, 1),
            "cp":       sanitize_int(request.form.get("cp"), 0, 3, 0),
            "trestbps": sanitize_int(request.form.get("trestbps"), 80, 250, 130),
            "chol":     sanitize_int(request.form.get("chol"), 100, 600, 240),
            "fbs":      sanitize_int(request.form.get("fbs"), 0, 1, 0),
            "restecg":  sanitize_int(request.form.get("restecg"), 0, 2, 0),
            "thalach":  sanitize_int(request.form.get("thalach"), 60, 220, 150),
            "exang":    sanitize_int(request.form.get("exang"), 0, 1, 0),
            "oldpeak":  sanitize_float(request.form.get("oldpeak"), 0.0, 10.0, 0.0),
            "slope":    sanitize_int(request.form.get("slope"), 0, 2, 1),
            "ca":       sanitize_int(request.form.get("ca"), 0, 3, 0),
            "thal":     sanitize_int(request.form.get("thal"), 1, 3, 2),
        }
        note = request.form.get("note", "").strip()[:500]

        result = predict_heart_disease(form)
        result["input_data"] = form
        result["note"]       = note
        result["timestamp"]  = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        log_audit_event("HEART_PREDICTION", session.get("username"),
                        {"diagnosis": result["diagnosis"],
                         "probability": result["probability"]})

        _add_history({
            "type":        "Heart Disease",
            "diagnosis":   result["diagnosis"],
            "probability": result["probability"],
            "timestamp":   result["timestamp"],
        })

        return render_template("results.html", result=result, mode="heart")

    return render_template("heart_form.html")


# ─────────────────────────────────────────────────────────────────────
# MODEL METRICS PAGE
# ─────────────────────────────────────────────────────────────────────
@app.route("/metrics")
@login_required
def metrics_page():
    metrics = get_model_metrics()
    return render_template("metrics.html", metrics=metrics)


# ─────────────────────────────────────────────────────────────────────
# HISTORY PAGE
# ─────────────────────────────────────────────────────────────────────
@app.route("/history")
@login_required
def history_page():
    history = _get_history()
    return render_template("history.html", history=history)


# ─────────────────────────────────────────────────────────────────────
# API — JSON endpoint for integration
# ─────────────────────────────────────────────────────────────────────
@app.route("/api/symptoms", methods=["GET"])
@login_required
def api_symptoms():
    return jsonify({"symptoms": get_all_symptoms()})

@app.route("/api/metrics", methods=["GET"])
@login_required
def api_metrics():
    return jsonify(get_model_metrics())


# ─────────────────────────────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404,
                           message="Page not found."), 404

@app.errorhandler(429)
def rate_limited(e):
    return render_template("error.html", code=429,
                           message="Too many requests. Please slow down."), 429

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500,
                           message="Internal server error."), 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
