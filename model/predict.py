"""
Healthcare AI - Prediction & Explainability Engine
Provides model inference + feature-importance-based explanations
(SHAP-compatible interface using RF feature importances × input contribution).
"""
import os, json
import numpy as np
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

# ── Lazy-load models ──────────────────────────────────────────────────
_hd_pipeline   = None
_sd_pipeline   = None
_label_encoder = None
_hd_meta       = None
_sd_meta       = None

def _load_heart_disease():
    global _hd_pipeline, _hd_meta
    if _hd_pipeline is None:
        _hd_pipeline = joblib.load(os.path.join(MODEL_DIR, "heart_disease_model.pkl"))
        with open(os.path.join(MODEL_DIR, "heart_disease_meta.json")) as f:
            _hd_meta = json.load(f)
    return _hd_pipeline, _hd_meta

def _load_symptom_disease():
    global _sd_pipeline, _label_encoder, _sd_meta
    if _sd_pipeline is None:
        _sd_pipeline   = joblib.load(os.path.join(MODEL_DIR, "symptom_disease_model.pkl"))
        _label_encoder = joblib.load(os.path.join(MODEL_DIR, "label_encoder.pkl"))
        with open(os.path.join(MODEL_DIR, "symptom_disease_meta.json")) as f:
            _sd_meta = json.load(f)
    return _sd_pipeline, _label_encoder, _sd_meta


# ── Explanation Helpers ───────────────────────────────────────────────
def _build_explanation(feature_names, input_values, feature_importances, top_n=5):
    """
    Local explanation: multiply global RF importances by whether the
    feature is active/present, then rank.  Simple and interpretable.
    """
    contributions = []
    for name, val, imp in zip(feature_names, input_values, feature_importances):
        if val != 0:
            contributions.append({
                'feature':      name,
                'value':        float(val),
                'contribution': round(float(imp) * abs(float(val)), 5)
            })

    # Sort by contribution descending
    contributions.sort(key=lambda x: x['contribution'], reverse=True)
    return contributions[:top_n]


RISK_LEVELS = {
    (0.00, 0.20): ('low',     'Low Risk',      '#22c55e'),
    (0.20, 0.40): ('low',     'Low-Moderate',  '#84cc16'),
    (0.40, 0.60): ('medium',  'Moderate Risk', '#f59e0b'),
    (0.60, 0.80): ('high',    'High Risk',     '#f97316'),
    (0.80, 1.01): ('critical','Critical Risk', '#ef4444'),
}

def _risk_level(prob):
    for (lo, hi), info in RISK_LEVELS.items():
        if lo <= prob < hi:
            return info
    return ('high', 'High Risk', '#ef4444')


DISEASE_INFO = {
    "Influenza":         {"specialist": "General Physician", "urgency": "Within 24–48 hrs", "icon": "🤧"},
    "COVID-19":          {"specialist": "Infectious Disease Specialist", "urgency": "Immediately", "icon": "🦠"},
    "Pneumonia":         {"specialist": "Pulmonologist", "urgency": "Same day", "icon": "🫁"},
    "Type 2 Diabetes":   {"specialist": "Endocrinologist", "urgency": "Within 1 week", "icon": "💉"},
    "Hypertension":      {"specialist": "Cardiologist", "urgency": "Within 48 hrs", "icon": "❤️"},
    "Migraine":          {"specialist": "Neurologist", "urgency": "When recurring", "icon": "🧠"},
    "Anemia":            {"specialist": "Hematologist", "urgency": "Within 1 week", "icon": "🩸"},
    "Hypothyroidism":    {"specialist": "Endocrinologist", "urgency": "Within 2 weeks", "icon": "🦋"},
    "GERD":              {"specialist": "Gastroenterologist", "urgency": "Non-urgent", "icon": "🔥"},
    "Asthma":            {"specialist": "Pulmonologist", "urgency": "Same day if severe", "icon": "💨"},
    "UTI":               {"specialist": "Urologist / GP", "urgency": "Within 24 hrs", "icon": "🚿"},
    "Dengue Fever":      {"specialist": "Infectious Disease Specialist", "urgency": "Immediately", "icon": "🦟"},
    "Appendicitis":      {"specialist": "General Surgeon", "urgency": "Emergency — NOW", "icon": "⚠️"},
    "Depression":        {"specialist": "Psychiatrist / Psychologist", "urgency": "Within 1 week", "icon": "💙"},
    "Hyperthyroidism":   {"specialist": "Endocrinologist", "urgency": "Within 1 week", "icon": "⚡"},
    "Heart Disease":     {"specialist": "Cardiologist", "urgency": "Immediately", "icon": "❤️"},
    "No Heart Disease":  {"specialist": "Continue Routine Checkups", "urgency": "Routine", "icon": "✅"},
}


# ── PUBLIC API ────────────────────────────────────────────────────────

def predict_heart_disease(form_data: dict) -> dict:
    """
    form_data keys: age, sex, cp, trestbps, chol, fbs, restecg,
                    thalach, exang, oldpeak, slope, ca, thal
    """
    pipeline, meta = _load_heart_disease()
    feature_cols  = meta['feature_cols']
    feature_names = meta['feature_names']

    # Build input vector
    X = np.array([[float(form_data.get(c, 0)) for c in feature_cols]])

    prob    = float(pipeline.predict_proba(X)[0][1])
    label   = meta['classes'][int(pipeline.predict(X)[0])]
    risk_id, risk_label, risk_color = _risk_level(prob)

    # Explanation: global importances × input
    fi   = meta['feature_importance']
    fi_vals = [fi.get(c, 0) for c in feature_cols]
    explanation = _build_explanation(
        feature_names=[feature_names.get(c, c) for c in feature_cols],
        input_values=X[0],
        feature_importances=fi_vals,
        top_n=6
    )

    info = DISEASE_INFO.get(label, {})
    return {
        'model':       'Heart Disease Classifier',
        'diagnosis':   label,
        'probability': round(prob * 100, 1),
        'risk_id':     risk_id,
        'risk_label':  risk_label,
        'risk_color':  risk_color,
        'specialist':  info.get('specialist', 'General Physician'),
        'urgency':     info.get('urgency', 'Consult a doctor'),
        'icon':        info.get('icon', '❤️'),
        'explanation': explanation,
        'metrics':     meta['metrics'],
        'disclaimer':  (
            "This AI prediction is for decision-support only. "
            "Always confirm with a qualified healthcare professional. "
            "Do not use this as a substitute for medical advice."
        ),
    }


def predict_symptom_disease(symptoms: list, age: int = 40, gender: str = "Unknown") -> dict:
    """
    symptoms: list of symptom string keys (e.g. ['fever','cough'])
    Returns top-3 differential diagnoses with probabilities.
    """
    pipeline, le, meta = _load_symptom_disease()
    symptom_cols = meta['symptom_cols']

    # Binary input vector
    X = np.zeros((1, len(symptom_cols)))
    for s in symptoms:
        if s in symptom_cols:
            X[0, symptom_cols.index(s)] = 1

    proba  = pipeline.predict_proba(X)[0]
    top3_idx = np.argsort(proba)[::-1][:3]

    differential = []
    for idx in top3_idx:
        disease_name = le.classes_[idx]
        p = proba[idx]
        info = DISEASE_INFO.get(disease_name, {})
        differential.append({
            'disease':    disease_name,
            'probability': round(float(p) * 100, 1),
            'risk_id':    _risk_level(p)[0],
            'risk_color': _risk_level(p)[2],
            'specialist': info.get('specialist', 'General Physician'),
            'urgency':    info.get('urgency', 'Consult a doctor'),
            'icon':       info.get('icon', '🏥'),
        })

    # Primary diagnosis
    primary = differential[0]

    # Explanation: which symptoms contributed most
    fi      = meta['feature_importance']
    fi_vals = [fi.get(c, 0) for c in symptom_cols]
    expl    = _build_explanation(
        feature_names=[c.replace('_',' ').title() for c in symptom_cols],
        input_values=X[0],
        feature_importances=fi_vals,
        top_n=5
    )

    return {
        'model':          'Symptom-Disease Classifier',
        'primary_diagnosis': primary['disease'],
        'probability':    primary['probability'],
        'risk_id':        primary['risk_id'],
        'risk_color':     primary['risk_color'],
        'icon':           primary['icon'],
        'specialist':     primary['specialist'],
        'urgency':        primary['urgency'],
        'differential':   differential,
        'explanation':    expl,
        'active_symptoms': symptoms,
        'metrics':        meta['metrics'],
        'disclaimer':     (
            "This AI prediction is for decision-support only. "
            "Always confirm with a qualified healthcare professional."
        ),
    }


def get_all_symptoms():
    _, _, meta = _load_symptom_disease()
    return meta['symptom_cols']


def get_model_metrics():
    _, hd_meta = _load_heart_disease()
    _, _, sd_meta = _load_symptom_disease()
    return {
        'heart_disease':    hd_meta['metrics'],
        'symptom_disease':  sd_meta['metrics'],
    }
