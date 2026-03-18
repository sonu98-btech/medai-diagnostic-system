"""
Healthcare AI — Test Suite
Tests model inference, input validation, and security utilities.
Run: python3 -m pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np

# ── Model Tests ───────────────────────────────────────────────
class TestHeartDiseaseModel:
    def test_high_risk_prediction(self):
        from model.predict import predict_heart_disease
        # Classic high-risk profile
        result = predict_heart_disease({
            'age': 65, 'sex': 1, 'cp': 0, 'trestbps': 160,
            'chol': 320, 'fbs': 1, 'restecg': 2, 'thalach': 100,
            'exang': 1, 'oldpeak': 4.0, 'slope': 2, 'ca': 3, 'thal': 3
        })
        assert result['probability'] > 50, "High-risk profile should have > 50% probability"
        assert result['diagnosis'] == 'Heart Disease'
        assert result['risk_id'] in ('high', 'critical', 'medium')
        assert len(result['explanation']) > 0
        assert 'disclaimer' in result

    def test_low_risk_prediction(self):
        from model.predict import predict_heart_disease
        # Classic low-risk profile
        result = predict_heart_disease({
            'age': 35, 'sex': 0, 'cp': 3, 'trestbps': 110,
            'chol': 180, 'fbs': 0, 'restecg': 0, 'thalach': 185,
            'exang': 0, 'oldpeak': 0.0, 'slope': 0, 'ca': 0, 'thal': 2
        })
        assert result['probability'] < 60, "Low-risk profile should have lower probability"
        assert 'metrics' in result

    def test_result_structure(self):
        from model.predict import predict_heart_disease
        result = predict_heart_disease({
            'age': 50, 'sex': 1, 'cp': 1, 'trestbps': 130,
            'chol': 240, 'fbs': 0, 'restecg': 0, 'thalach': 150,
            'exang': 0, 'oldpeak': 1.0, 'slope': 1, 'ca': 0, 'thal': 2
        })
        required = ['model', 'diagnosis', 'probability', 'risk_id', 'risk_color',
                    'risk_label', 'specialist', 'urgency', 'explanation', 'metrics']
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_probability_range(self):
        from model.predict import predict_heart_disease
        result = predict_heart_disease({
            'age': 50, 'sex': 1, 'cp': 1, 'trestbps': 130,
            'chol': 240, 'fbs': 0, 'restecg': 0, 'thalach': 150,
            'exang': 0, 'oldpeak': 1.0, 'slope': 1, 'ca': 0, 'thal': 2
        })
        assert 0 <= result['probability'] <= 100


class TestSymptomDiseaseModel:
    def test_flu_prediction(self):
        from model.predict import predict_symptom_disease
        result = predict_symptom_disease(
            ['fever', 'cough', 'fatigue', 'muscle_pain', 'headache', 'runny_nose'],
            age=30, gender='Female'
        )
        assert result['primary_diagnosis'] in (
            'Influenza', 'COVID-19', 'Dengue Fever'
        ), f"Flu-like symptoms should predict respiratory disease, got {result['primary_diagnosis']}"

    def test_diabetes_prediction(self):
        from model.predict import predict_symptom_disease
        result = predict_symptom_disease(
            ['excessive_thirst', 'frequent_urination', 'fatigue', 'blurred_vision', 'weight_loss'],
            age=50
        )
        assert result['primary_diagnosis'] == 'Type 2 Diabetes', \
            f"Diabetes symptoms should predict diabetes, got {result['primary_diagnosis']}"

    def test_differential_count(self):
        from model.predict import predict_symptom_disease
        result = predict_symptom_disease(['fever', 'headache', 'fatigue'])
        assert len(result['differential']) == 3

    def test_empty_symptoms(self):
        from model.predict import predict_symptom_disease
        # Should not crash on empty (predicts with near-uniform distribution)
        result = predict_symptom_disease([])
        assert 'primary_diagnosis' in result

    def test_result_structure(self):
        from model.predict import predict_symptom_disease
        result = predict_symptom_disease(['fever', 'cough'])
        for key in ['model', 'primary_diagnosis', 'probability', 'differential',
                    'explanation', 'specialist', 'urgency', 'metrics']:
            assert key in result


class TestSymptomList:
    def test_symptom_list_nonempty(self):
        from model.predict import get_all_symptoms
        symptoms = get_all_symptoms()
        assert len(symptoms) > 30

    def test_symptoms_are_strings(self):
        from model.predict import get_all_symptoms
        symptoms = get_all_symptoms()
        assert all(isinstance(s, str) for s in symptoms)


# ── Security Tests ────────────────────────────────────────────
class TestSecurity:
    def test_sanitize_float_valid(self):
        from utils.security import sanitize_float
        assert sanitize_float("1.5", 0, 10, 0) == 1.5

    def test_sanitize_float_out_of_range(self):
        from utils.security import sanitize_float
        assert sanitize_float("999", 0, 10, 5.0) == 5.0

    def test_sanitize_float_invalid(self):
        from utils.security import sanitize_float
        assert sanitize_float("abc", 0, 10, 3.0) == 3.0

    def test_sanitize_int_valid(self):
        from utils.security import sanitize_int
        assert sanitize_int("55", 0, 120, 40) == 55

    def test_sanitize_int_out_of_range(self):
        from utils.security import sanitize_int
        assert sanitize_int("-5", 0, 120, 40) == 40

    def test_sanitize_symptoms_whitelist(self):
        from utils.security import sanitize_symptoms
        valid = ['fever', 'cough', 'headache']
        result = sanitize_symptoms(['fever', 'cough', '<script>alert(1)</script>'], valid)
        assert result == ['fever', 'cough']
        assert '<script>alert(1)</script>' not in result

    def test_sanitize_symptoms_empty(self):
        from utils.security import sanitize_symptoms
        result = sanitize_symptoms([], ['fever', 'cough'])
        assert result == []

    def test_verify_user_valid(self):
        # Patch request context
        from unittest.mock import patch, MagicMock
        import flask
        app = flask.Flask(__name__)
        with app.test_request_context('/'):
            from utils.security import verify_user
            assert verify_user('doctor', 'clinic2024') is True

    def test_verify_user_invalid(self):
        from unittest.mock import patch
        import flask
        app = flask.Flask(__name__)
        with app.test_request_context('/'):
            from utils.security import verify_user
            assert verify_user('doctor', 'wrongpassword') is False

    def test_rate_limit_allows_normal(self):
        from utils.security import check_rate_limit, _rate_buckets
        _rate_buckets.clear()
        for _ in range(5):
            assert check_rate_limit("test-client-abc") is True

    def test_rate_limit_blocks_excess(self):
        from utils.security import check_rate_limit, _rate_buckets, MAX_REQUESTS_PER_MIN
        import time
        _rate_buckets.clear()
        # Fill bucket
        client = "heavy-client-xyz"
        for _ in range(MAX_REQUESTS_PER_MIN):
            check_rate_limit(client)
        # Next should be blocked
        assert check_rate_limit(client) is False


# ── Dataset Tests ─────────────────────────────────────────────
class TestDatasets:
    def test_heart_disease_csv_exists(self):
        assert os.path.exists('data/heart_disease.csv')

    def test_symptom_csv_exists(self):
        assert os.path.exists('data/symptom_disease.csv')

    def test_heart_disease_shape(self):
        import pandas as pd
        df = pd.read_csv('data/heart_disease.csv')
        assert df.shape[0] >= 1000
        assert 'target' in df.columns
        assert df['target'].isin([0, 1]).all()

    def test_symptom_disease_shape(self):
        import pandas as pd
        df = pd.read_csv('data/symptom_disease.csv')
        assert df.shape[0] >= 1000
        assert 'disease' in df.columns
        assert df['disease'].nunique() == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
