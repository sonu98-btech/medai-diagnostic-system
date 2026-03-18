"""
Healthcare AI - Model Training Pipeline
Trains two models:
  1. Heart Disease Classifier (binary, tabular)
  2. Symptom-Disease Classifier (multi-class, tabular)

Uses Random Forest with hyperparameter tuning.
Saves models + metadata for serving.
"""
import os, json, joblib, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_val_score, GridSearchCV
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve
)
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
warnings.filterwarnings("ignore")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "model", "artifacts")
PLOT_DIR  = os.path.join(os.path.dirname(__file__), "..", "static", "img", "plots")
DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PLOT_DIR,  exist_ok=True)


# ─────────────────────────────────────────────────────────────────────
# HEART DISEASE MODEL
# ─────────────────────────────────────────────────────────────────────
def train_heart_disease_model():
    print("\n" + "="*60)
    print("  TRAINING: Heart Disease Classifier")
    print("="*60)

    df = pd.read_csv(os.path.join(DATA_DIR, "heart_disease.csv"))
    FEATURE_COLS = ['age','sex','cp','trestbps','chol','fbs','restecg',
                    'thalach','exang','oldpeak','slope','ca','thal']
    FEATURE_NAMES = {
        'age':       'Age',
        'sex':       'Sex (1=Male, 0=Female)',
        'cp':        'Chest Pain Type (0-3)',
        'trestbps':  'Resting Blood Pressure (mmHg)',
        'chol':      'Serum Cholesterol (mg/dL)',
        'fbs':       'Fasting Blood Sugar > 120 mg/dL',
        'restecg':   'Resting ECG Results (0-2)',
        'thalach':   'Maximum Heart Rate',
        'exang':     'Exercise Induced Angina',
        'oldpeak':   'ST Depression (Exercise vs Rest)',
        'slope':     'Slope of Peak Exercise ST Segment',
        'ca':        'Number of Major Vessels (0-3)',
        'thal':      'Thalassemia (1=Normal, 2=Fixed Defect, 3=Reversible)'
    }

    X = df[FEATURE_COLS].values
    y = df['target'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Build pipeline
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler',  StandardScaler()),
        ('clf',     RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=4,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ))
    ])

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring='roc_auc', n_jobs=-1)
    print(f"  CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Train final model
    pipeline.fit(X_train, y_train)
    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        'accuracy':  round(accuracy_score(y_test, y_pred), 4),
        'precision': round(precision_score(y_test, y_pred), 4),
        'recall':    round(recall_score(y_test, y_pred), 4),
        'f1':        round(f1_score(y_test, y_pred), 4),
        'auc_roc':   round(roc_auc_score(y_test, y_proba), 4),
        'cv_auc_mean': round(cv_scores.mean(), 4),
        'cv_auc_std':  round(cv_scores.std(), 4),
    }
    print(f"  Accuracy : {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall   : {metrics['recall']:.4f}")
    print(f"  F1-Score : {metrics['f1']:.4f}")
    print(f"  AUC-ROC  : {metrics['auc_roc']:.4f}")

    # Feature importances
    rf_model = pipeline.named_steps['clf']
    importances = rf_model.feature_importances_
    feat_imp = dict(zip(FEATURE_COLS, importances.tolist()))

    # ─── Plot 1: Confusion Matrix ────────────────────────────────────
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4), facecolor='#0d1117')
    ax.set_facecolor('#0d1117')
    sns.heatmap(cm, annot=True, fmt='d', cmap='YlOrRd',
                xticklabels=['No Disease','Disease'],
                yticklabels=['No Disease','Disease'],
                ax=ax, linewidths=0.5,
                annot_kws={'size': 14, 'color': 'white'})
    ax.set_title('Heart Disease — Confusion Matrix', color='white', fontsize=13, pad=12)
    ax.set_xlabel('Predicted', color='#aaa', fontsize=10)
    ax.set_ylabel('Actual', color='#aaa', fontsize=10)
    ax.tick_params(colors='#aaa')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "hd_confusion.png"), dpi=120, bbox_inches='tight',
                facecolor='#0d1117')
    plt.close()

    # ─── Plot 2: ROC Curve ───────────────────────────────────────────
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    fig, ax = plt.subplots(figsize=(5, 4), facecolor='#0d1117')
    ax.set_facecolor('#0d1117')
    ax.plot(fpr, tpr, color='#e05c5c', lw=2, label=f'AUC = {metrics["auc_roc"]:.3f}')
    ax.plot([0,1],[0,1], 'w--', lw=0.8, alpha=0.5)
    ax.set_xlabel('False Positive Rate', color='#aaa')
    ax.set_ylabel('True Positive Rate', color='#aaa')
    ax.set_title('Heart Disease — ROC Curve', color='white', fontsize=13)
    ax.legend(facecolor='#1a1f2e', edgecolor='#333', labelcolor='white')
    ax.tick_params(colors='#aaa')
    ax.spines[:].set_color('#333')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "hd_roc.png"), dpi=120, bbox_inches='tight',
                facecolor='#0d1117')
    plt.close()

    # ─── Plot 3: Feature Importance ─────────────────────────────────
    sorted_feats = sorted(feat_imp.items(), key=lambda x: x[1], reverse=True)
    feat_labels = [FEATURE_NAMES.get(f, f) for f, _ in sorted_feats]
    feat_vals   = [v for _, v in sorted_feats]

    fig, ax = plt.subplots(figsize=(7, 5), facecolor='#0d1117')
    ax.set_facecolor('#0d1117')
    bars = ax.barh(feat_labels[::-1], feat_vals[::-1], color='#e05c5c', edgecolor='none', height=0.65)
    ax.set_title('Heart Disease — Feature Importance', color='white', fontsize=13, pad=10)
    ax.set_xlabel('Importance', color='#aaa')
    ax.tick_params(colors='#aaa', labelsize=9)
    ax.spines[:].set_color('#333')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "hd_importance.png"), dpi=120, bbox_inches='tight',
                facecolor='#0d1117')
    plt.close()

    # Save
    joblib.dump(pipeline, os.path.join(MODEL_DIR, "heart_disease_model.pkl"))
    artifact = {
        'feature_cols':   FEATURE_COLS,
        'feature_names':  FEATURE_NAMES,
        'feature_importance': feat_imp,
        'metrics':        metrics,
        'classes':        ['No Heart Disease', 'Heart Disease'],
        'model_type':     'RandomForestClassifier',
        'task':           'binary_classification',
    }
    with open(os.path.join(MODEL_DIR, "heart_disease_meta.json"), "w") as f:
        json.dump(artifact, f, indent=2)

    print(f"  Model saved ✓")
    return metrics


# ─────────────────────────────────────────────────────────────────────
# SYMPTOM-DISEASE MODEL
# ─────────────────────────────────────────────────────────────────────
def train_symptom_disease_model():
    print("\n" + "="*60)
    print("  TRAINING: Symptom-Disease Classifier")
    print("="*60)

    df = pd.read_csv(os.path.join(DATA_DIR, "symptom_disease.csv"))

    SYMPTOM_COLS = [c for c in df.columns if c not in ('disease','age','gender')]
    X = df[SYMPTOM_COLS].values
    y_raw = df['disease'].values

    le = LabelEncoder()
    y  = le.fit_transform(y_raw)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('clf',     RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ))
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring='accuracy', n_jobs=-1)
    print(f"  CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)

    metrics = {
        'accuracy':           round(accuracy_score(y_test, y_pred), 4),
        'macro_precision':    round(precision_score(y_test, y_pred, average='macro', zero_division=0), 4),
        'macro_recall':       round(recall_score(y_test, y_pred, average='macro', zero_division=0), 4),
        'macro_f1':           round(f1_score(y_test, y_pred, average='macro', zero_division=0), 4),
        'cv_acc_mean':        round(cv_scores.mean(), 4),
        'cv_acc_std':         round(cv_scores.std(), 4),
    }
    print(f"  Accuracy : {metrics['accuracy']:.4f}")
    print(f"  Macro F1 : {metrics['macro_f1']:.4f}")

    # Feature importances per disease
    rf_model = pipeline.named_steps['clf']
    importances = rf_model.feature_importances_
    feat_imp = dict(zip(SYMPTOM_COLS, importances.tolist()))
    top_symptoms = sorted(feat_imp.items(), key=lambda x: x[1], reverse=True)[:10]

    # ─── Plot: Top-10 Symptom Importances ───────────────────────────
    labels = [s.replace('_', ' ').title() for s, _ in top_symptoms]
    vals   = [v for _, v in top_symptoms]

    fig, ax = plt.subplots(figsize=(7, 5), facecolor='#0d1117')
    ax.set_facecolor('#0d1117')
    colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(vals)))
    ax.barh(labels[::-1], vals[::-1], color=colors, edgecolor='none', height=0.65)
    ax.set_title('Top 10 Diagnostic Symptom Features', color='white', fontsize=13, pad=10)
    ax.set_xlabel('Feature Importance', color='#aaa')
    ax.tick_params(colors='#aaa', labelsize=9)
    ax.spines[:].set_color('#333')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "sd_importance.png"), dpi=120, bbox_inches='tight',
                facecolor='#0d1117')
    plt.close()

    # Save
    joblib.dump(pipeline, os.path.join(MODEL_DIR, "symptom_disease_model.pkl"))
    joblib.dump(le,       os.path.join(MODEL_DIR, "label_encoder.pkl"))
    artifact = {
        'symptom_cols':       SYMPTOM_COLS,
        'classes':            le.classes_.tolist(),
        'feature_importance': feat_imp,
        'metrics':            metrics,
        'model_type':         'RandomForestClassifier',
        'task':               'multi_class_classification',
    }
    with open(os.path.join(MODEL_DIR, "symptom_disease_meta.json"), "w") as f:
        json.dump(artifact, f, indent=2)

    print(f"  Model saved ✓")
    return metrics


if __name__ == "__main__":
    hd_metrics = train_heart_disease_model()
    sd_metrics = train_symptom_disease_model()

    print("\n" + "="*60)
    print("  TRAINING COMPLETE")
    print("="*60)
    print(f"  Heart Disease  — Accuracy: {hd_metrics['accuracy']:.4f}  AUC: {hd_metrics['auc_roc']:.4f}")
    print(f"  Symptom-Disease — Accuracy: {sd_metrics['accuracy']:.4f}  F1: {sd_metrics['macro_f1']:.4f}")
    print("="*60)
