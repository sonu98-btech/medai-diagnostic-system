"""
Healthcare AI Dataset Generator
Generates synthetic datasets based on real-world clinical distributions
from UCI Heart Disease & public symptom-disease datasets.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import os

np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────
# 1. HEART DISEASE DATASET (UCI Cleveland distribution)
# ─────────────────────────────────────────────────────────────────────
def generate_heart_disease_dataset(n=2000):
    age = np.random.normal(54, 9, n).clip(29, 77).astype(int)
    sex = np.random.binomial(1, 0.68, n)
    cp = np.random.choice([0, 1, 2, 3], n, p=[0.47, 0.17, 0.28, 0.08])
    trestbps = np.random.normal(131, 17, n).clip(94, 200).astype(int)
    chol = np.random.normal(246, 52, n).clip(126, 564).astype(int)
    fbs = np.random.binomial(1, 0.15, n)
    restecg = np.random.choice([0, 1, 2], n, p=[0.48, 0.49, 0.03])
    thalach = np.random.normal(149, 23, n).clip(71, 202).astype(int)
    exang = np.random.binomial(1, 0.33, n)
    oldpeak = np.round(np.random.exponential(1.0, n).clip(0, 6.2), 1)
    slope = np.random.choice([0, 1, 2], n, p=[0.07, 0.46, 0.47])
    ca = np.random.choice([0, 1, 2, 3], n, p=[0.59, 0.22, 0.13, 0.06])
    thal = np.random.choice([1, 2, 3], n, p=[0.06, 0.55, 0.39])

    # Risk score → target (realistic clinical logic)
    risk = (
        0.3 * (age > 55) +
        0.2 * sex +
        0.25 * (cp == 0) +
        0.15 * (trestbps > 140) +
        0.1 * (chol > 240) +
        0.1 * fbs +
        0.2 * exang +
        0.3 * (oldpeak > 2) +
        0.25 * (ca > 0) +
        0.2 * (thal == 3) +
        0.1 * (thalach < 140) +
        np.random.normal(0, 0.15, n)
    )
    target = (risk > 0.85).astype(int)

    df = pd.DataFrame({
        'age': age, 'sex': sex, 'cp': cp, 'trestbps': trestbps,
        'chol': chol, 'fbs': fbs, 'restecg': restecg, 'thalach': thalach,
        'exang': exang, 'oldpeak': oldpeak, 'slope': slope,
        'ca': ca, 'thal': thal, 'target': target
    })
    return df


# ─────────────────────────────────────────────────────────────────────
# 2. SYMPTOM-DISEASE DATASET (multi-class, 15 diseases)
# ─────────────────────────────────────────────────────────────────────
DISEASES = [
    "Influenza", "COVID-19", "Pneumonia", "Type 2 Diabetes",
    "Hypertension", "Migraine", "Anemia", "Hypothyroidism",
    "GERD", "Asthma", "UTI", "Dengue Fever",
    "Appendicitis", "Depression", "Hyperthyroidism"
]

ALL_SYMPTOMS = [
    "fever", "cough", "fatigue", "shortness_of_breath", "chest_pain",
    "headache", "nausea", "vomiting", "diarrhea", "abdominal_pain",
    "muscle_pain", "joint_pain", "loss_of_taste", "loss_of_smell",
    "runny_nose", "sore_throat", "back_pain", "dizziness", "weight_loss",
    "weight_gain", "excessive_thirst", "frequent_urination", "blurred_vision",
    "cold_intolerance", "heat_intolerance", "palpitations", "sweating",
    "skin_rash", "burning_sensation_urination", "anxiety", "sadness",
    "insomnia", "appetite_loss", "constipation", "heartburn", "wheezing",
    "night_sweats", "tremors", "bleeding_gums"
]

DISEASE_PROFILES = {
    "Influenza":          {"fever": 0.9, "cough": 0.85, "fatigue": 0.8, "muscle_pain": 0.75,
                           "headache": 0.7, "sore_throat": 0.65, "runny_nose": 0.7},
    "COVID-19":           {"fever": 0.8, "cough": 0.8, "fatigue": 0.75, "loss_of_taste": 0.7,
                           "loss_of_smell": 0.7, "shortness_of_breath": 0.6, "headache": 0.55},
    "Pneumonia":          {"fever": 0.85, "cough": 0.9, "shortness_of_breath": 0.8,
                           "chest_pain": 0.65, "fatigue": 0.75, "sweating": 0.6},
    "Type 2 Diabetes":    {"excessive_thirst": 0.85, "frequent_urination": 0.85, "fatigue": 0.7,
                           "blurred_vision": 0.6, "weight_loss": 0.55, "headache": 0.4},
    "Hypertension":       {"headache": 0.7, "dizziness": 0.65, "chest_pain": 0.5,
                           "shortness_of_breath": 0.45, "blurred_vision": 0.4},
    "Migraine":           {"headache": 0.95, "nausea": 0.75, "vomiting": 0.6,
                           "dizziness": 0.55, "blurred_vision": 0.5, "fatigue": 0.5},
    "Anemia":             {"fatigue": 0.9, "dizziness": 0.75, "shortness_of_breath": 0.7,
                           "headache": 0.6, "cold_intolerance": 0.55, "palpitations": 0.5},
    "Hypothyroidism":     {"fatigue": 0.85, "weight_gain": 0.8, "cold_intolerance": 0.8,
                           "constipation": 0.65, "sadness": 0.55, "insomnia": 0.4},
    "GERD":               {"heartburn": 0.9, "chest_pain": 0.65, "nausea": 0.6,
                           "vomiting": 0.4, "sore_throat": 0.5, "cough": 0.45},
    "Asthma":             {"wheezing": 0.9, "shortness_of_breath": 0.85, "cough": 0.8,
                           "chest_pain": 0.55, "fatigue": 0.5},
    "UTI":                {"burning_sensation_urination": 0.9, "frequent_urination": 0.85,
                           "abdominal_pain": 0.6, "fever": 0.55, "nausea": 0.4},
    "Dengue Fever":       {"fever": 0.95, "headache": 0.8, "muscle_pain": 0.8,
                           "joint_pain": 0.75, "skin_rash": 0.65, "bleeding_gums": 0.5, "fatigue": 0.7},
    "Appendicitis":       {"abdominal_pain": 0.95, "nausea": 0.75, "vomiting": 0.65,
                           "fever": 0.7, "appetite_loss": 0.6},
    "Depression":         {"sadness": 0.9, "fatigue": 0.85, "insomnia": 0.75,
                           "appetite_loss": 0.7, "anxiety": 0.65, "weight_loss": 0.4},
    "Hyperthyroidism":    {"weight_loss": 0.8, "heat_intolerance": 0.8, "palpitations": 0.75,
                           "anxiety": 0.7, "tremors": 0.65, "sweating": 0.65, "diarrhea": 0.5},
}

def generate_symptom_dataset(n_per_disease=200):
    rows = []
    for disease, profile in DISEASE_PROFILES.items():
        for _ in range(n_per_disease):
            row = {sym: 0 for sym in ALL_SYMPTOMS}
            # Apply disease profile probabilities
            for sym, prob in profile.items():
                row[sym] = int(np.random.random() < prob)
            # Random noise symptoms (comorbidities)
            for sym in ALL_SYMPTOMS:
                if row[sym] == 0 and np.random.random() < 0.05:
                    row[sym] = 1
            row['disease'] = disease
            # Metadata
            row['age'] = int(np.random.normal(45, 15, 1).clip(18, 85)[0])
            row['gender'] = np.random.choice(['Male', 'Female'])
            rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    
    hd = generate_heart_disease_dataset(2000)
    hd.to_csv("data/heart_disease.csv", index=False)
    print(f"Heart disease dataset: {hd.shape}, positive rate: {hd.target.mean():.2%}")
    
    sd = generate_symptom_dataset(200)
    sd.to_csv("data/symptom_disease.csv", index=False)
    print(f"Symptom dataset: {sd.shape}, {sd.disease.nunique()} diseases")
    print("Datasets saved.")
