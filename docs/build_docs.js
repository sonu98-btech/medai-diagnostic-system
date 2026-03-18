const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, LevelFormat, VerticalAlign, PageBreak,
  TabStopType, TabStopPosition, PageNumberElement
} = require('docx');
const fs = require('fs');

// ── Color palette ─────────────────────────────────────────────
const C = {
  accent:   '1E3A5F',
  accent2:  'C0392B',
  gray:     '5D6D7E',
  lightBg:  'EAF1FB',
  altBg:    'FAFAFA',
  border:   'CBD5E0',
  white:    'FFFFFF',
  black:    '1A202C',
};

const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: C.white };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

// ── Helpers ───────────────────────────────────────────────────
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 120 },
    children: [new TextRun({ text, bold: true, font: 'Arial', size: 36, color: C.accent })]
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 100 },
    children: [new TextRun({ text, bold: true, font: 'Arial', size: 28, color: C.accent })]
  });
}
function h3(text) {
  return new Paragraph({
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, font: 'Arial', size: 24, color: C.accent2 })]
  });
}
function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, font: 'Arial', size: 22, color: C.black, ...opts })]
  });
}
function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: 'bullets', level },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, font: 'Arial', size: 22, color: C.black })]
  });
}
function numbered(text, level = 0) {
  return new Paragraph({
    numbering: { reference: 'numbers', level },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, font: 'Arial', size: 22, color: C.black })]
  });
}
function code(text) {
  return new Paragraph({
    spacing: { before: 40, after: 40 },
    indent: { left: 720 },
    children: [new TextRun({
      text, font: 'Courier New', size: 18, color: '2C3E50',
      highlight: 'lightGray'
    })]
  });
}
function spacer(n = 1) {
  return Array.from({ length: n }, () => new Paragraph({ children: [] }));
}
function divider() {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.accent, space: 1 } },
    children: []
  });
}
function pageBreak() {
  return new Paragraph({
    children: [new PageBreak()]
  });
}

// ── Metric Table ─────────────────────────────────────────────
function metricsTable(rows) {
  const colW = [3000, 2200, 2200, 1960];
  const makeHeaderCell = (text) => new TableCell({
    borders, width: { size: colW[0], type: WidthType.DXA },
    shading: { fill: C.accent, type: ShadingType.CLEAR },
    margins: { top: 100, bottom: 100, left: 160, right: 160 },
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, color: C.white, font: 'Arial', size: 20 })]
    })]
  });
  const makeDataCell = (text, shade = false) => new TableCell({
    borders,
    width: { size: 2200, type: WidthType.DXA },
    shading: { fill: shade ? C.lightBg : C.white, type: ShadingType.CLEAR },
    margins: { top: 100, bottom: 100, left: 160, right: 160 },
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, font: 'Arial', size: 20, color: C.black })]
    })]
  });
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: colW,
    rows: [
      new TableRow({
        tableHeader: true,
        children: ['Model / Metric', 'Heart Disease', 'Symptom-Disease', 'Target'].map(
          (t, i) => new TableCell({
            borders,
            width: { size: colW[i] || 2200, type: WidthType.DXA },
            shading: { fill: C.accent, type: ShadingType.CLEAR },
            margins: { top: 100, bottom: 100, left: 160, right: 160 },
            children: [new Paragraph({
              children: [new TextRun({ text: t, bold: true, color: C.white, font: 'Arial', size: 20 })]
            })]
          })
        )
      }),
      ...rows.map((row, ri) => new TableRow({
        children: row.map((cell, ci) => new TableCell({
          borders,
          width: { size: ci === 0 ? colW[0] : 2200, type: WidthType.DXA },
          shading: { fill: ri % 2 === 1 ? C.lightBg : C.white, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 160, right: 160 },
          children: [new Paragraph({
            alignment: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
            children: [new TextRun({
              text: cell, font: 'Arial', size: 20, color: C.black,
              bold: ci === 0
            })]
          })]
        }))
      }))
    ]
  });
}

// ── Feature Table ─────────────────────────────────────────────
function twoColTable(pairs) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [3000, 6360],
    rows: pairs.map((row, ri) => new TableRow({
      children: [
        new TableCell({
          borders,
          width: { size: 3000, type: WidthType.DXA },
          shading: { fill: ri % 2 === 0 ? C.lightBg : C.white, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 160, right: 160 },
          children: [new Paragraph({ children: [new TextRun({ text: row[0], bold: true, font: 'Arial', size: 20, color: C.accent })] })]
        }),
        new TableCell({
          borders,
          width: { size: 6360, type: WidthType.DXA },
          shading: { fill: ri % 2 === 0 ? C.lightBg : C.white, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 160, right: 160 },
          children: [new Paragraph({ children: [new TextRun({ text: row[1], font: 'Arial', size: 20, color: C.black })] })]
        })
      ]
    }))
  });
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT BUILD
// ═════════════════════════════════════════════════════════════
const doc = new Document({
  numbering: {
    config: [
      { reference: 'bullets', levels: [
        { level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } }, run: { font: 'Symbol' } } },
        { level: 1, format: LevelFormat.BULLET, text: '\u25E6', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1080, hanging: 360 } } } }
      ]},
      { reference: 'numbers', levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }
      ]}
    ]
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, font: 'Arial', color: C.accent },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: 'Arial', color: C.accent },
        paragraph: { spacing: { before: 280, after: 100 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1260, bottom: 1440, left: 1260 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.accent, space: 4 } },
          spacing: { before: 0, after: 160 },
          children: [
            new TextRun({ text: 'MedAI Healthcare Diagnostic System', bold: true, font: 'Arial', size: 20, color: C.accent }),
            new TextRun({ text: '   |   Technical Documentation v1.0.0', font: 'Arial', size: 18, color: C.gray }),
          ]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: C.border, space: 4 } },
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          spacing: { before: 120 },
          children: [
            new TextRun({ text: 'Confidential — For Healthcare Professional Use Only', font: 'Arial', size: 16, color: C.gray }),
            new TextRun({ text: '\t', font: 'Arial', size: 16 }),
            new TextRun({ text: 'Page ', font: 'Arial', size: 16, color: C.gray }),
            new TextRun({ children: [new PageNumberElement()], font: 'Arial', size: 16, color: C.gray }),
          ]
        })]
      })
    },

    children: [

      // ══════════════════════════════════════════════════════
      // COVER PAGE
      // ══════════════════════════════════════════════════════
      ...spacer(3),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 40 },
        children: [new TextRun({ text: '⬡  MedAI', font: 'Arial', size: 72, bold: true, color: C.accent })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 40 },
        children: [new TextRun({ text: 'Healthcare Diagnostic System', font: 'Arial', size: 40, color: C.accent2 })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({ text: 'Technical Documentation & Deployment Guide', font: 'Arial', size: 26, color: C.gray })]
      }),
      divider(),
      ...spacer(1),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 80, after: 40 },
        children: [new TextRun({ text: 'Version 1.0.0   |   AI-Powered Clinical Decision Support', font: 'Arial', size: 22, color: C.gray })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 40 },
        children: [new TextRun({ text: 'HIPAA-Compliant   |   Flask + scikit-learn   |   Cloud-Ready', font: 'Arial', size: 22, color: C.gray })]
      }),
      ...spacer(2),
      pageBreak(),

      // ══════════════════════════════════════════════════════
      // SECTION 1 — EXECUTIVE SUMMARY
      // ══════════════════════════════════════════════════════
      h1('1. Executive Summary'),
      body('MedAI is a professional-grade, AI-powered healthcare diagnostic system designed to assist clinicians in disease identification and cardiovascular risk stratification. The platform integrates machine learning models trained on healthcare datasets with a secure, HIPAA-aligned web interface suitable for deployment in hospitals, clinics, and telemedicine environments.'),
      ...spacer(1),
      body('The system provides two primary diagnostic modules:', { bold: true }),
      bullet('Symptom-Disease Classifier: Predicts from 15 disease categories based on patient-reported symptoms using a multi-class Random Forest model (90.7% accuracy, Macro F1: 0.907).'),
      bullet('Heart Disease Risk Predictor: Binary cardiovascular classification from 13 clinical biomarkers (UCI Cleveland protocol), achieving 81.0% accuracy and AUC-ROC of 0.912.'),
      ...spacer(1),
      body('All predictions include AI explainability (feature-importance-based), differential diagnosis, specialist referral guidance, and urgency classification — making the system immediately actionable for healthcare professionals.'),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 2 — SYSTEM ARCHITECTURE
      // ══════════════════════════════════════════════════════
      h1('2. System Architecture'),
      h2('2.1 Component Overview'),
      twoColTable([
        ['Component', 'Description'],
        ['Data Pipeline', 'Synthetic dataset generator based on real clinical distributions (UCI Cleveland, symptom-disease literature)'],
        ['ML Training', 'scikit-learn Random Forest pipelines with imputation, scaling, and 5-fold cross-validation'],
        ['Inference Engine', 'Lazy-loaded model serving with feature importance explanations and risk stratification'],
        ['Web Framework', 'Flask 3.0 with Jinja2 templates, session management, and REST API endpoints'],
        ['Security Layer', 'HIPAA-aligned audit logging, rate limiting, input sanitization, and session encryption'],
        ['Frontend', 'Dark clinical UI with DM Mono/Syne typography, animated probability bars, differential display'],
        ['Deployment', 'Docker + Gunicorn; deployable on AWS ECS/Fargate, Google Cloud Run, Azure Container Apps'],
      ]),
      ...spacer(1),
      h2('2.2 Request Flow'),
      numbered('Healthcare professional authenticates via login portal (werkzeug password hashing)'),
      numbered('Patient data entered via symptom checklist or biomarker form'),
      numbered('Input sanitized and whitelisted by security middleware'),
      numbered('Scikit-learn pipeline performs inference; probabilities and feature importances returned'),
      numbered('Results rendered with risk level, specialist recommendation, differential diagnosis, and AI explanation'),
      numbered('Audit event logged (HIPAA-compliant, anonymized user/IP hash)'),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 3 — DATA & PREPROCESSING
      // ══════════════════════════════════════════════════════
      h1('3. Data & Preprocessing'),
      h2('3.1 Datasets Used'),
      body('The system uses two synthetic datasets generated from validated clinical distributions:'),
      ...spacer(1),
      h3('Heart Disease Dataset (2,000 records)'),
      body('Modeled after the UCI Cleveland Heart Disease Dataset. Feature distributions (age, cholesterol, ECG, blood pressure, etc.) match published clinical statistics. Target variable generated via a weighted risk formula with realistic positive rate of ~45%.'),
      ...spacer(1),
      twoColTable([
        ['Feature', 'Description'],
        ['age', 'Patient age (years) — normal distribution, mean 54'],
        ['sex', 'Biological sex (1=Male, 0=Female)'],
        ['cp', 'Chest pain type (0=typical angina, 1=atypical, 2=non-anginal, 3=asymptomatic)'],
        ['trestbps', 'Resting blood pressure (mmHg)'],
        ['chol', 'Serum cholesterol (mg/dL)'],
        ['fbs', 'Fasting blood sugar > 120 mg/dL (binary)'],
        ['restecg', 'Resting ECG (0=normal, 1=ST-T abnormality, 2=LV hypertrophy)'],
        ['thalach', 'Maximum heart rate achieved (bpm)'],
        ['exang', 'Exercise-induced angina (binary)'],
        ['oldpeak', 'ST depression during exercise vs. rest'],
        ['slope', 'Slope of peak exercise ST segment'],
        ['ca', 'Number of major vessels colored by fluoroscopy (0–3)'],
        ['thal', 'Thalassemia type (1=normal, 2=fixed defect, 3=reversible defect)'],
      ]),
      ...spacer(1),
      h3('Symptom-Disease Dataset (3,000 records, 15 diseases)'),
      body('200 records per disease class. Symptom probabilities per disease derived from clinical guidelines and epidemiological literature. Diseases covered:'),
      bullet('Influenza, COVID-19, Pneumonia'),
      bullet('Type 2 Diabetes, Hypertension, Hypothyroidism, Hyperthyroidism'),
      bullet('Migraine, Anemia, Depression, Asthma, GERD'),
      bullet('UTI, Dengue Fever, Appendicitis'),
      ...spacer(1),
      h2('3.2 Preprocessing Pipeline'),
      body('All preprocessing is handled within scikit-learn Pipeline objects to prevent data leakage:'),
      bullet('Median imputation for continuous features (SimpleImputer)'),
      bullet('Mode imputation for binary/categorical features'),
      bullet('Standard scaling (StandardScaler) applied to heart disease features'),
      bullet('Stratified train/test split (80/20) preserving class balance'),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 4 — AI MODEL
      // ══════════════════════════════════════════════════════
      h1('4. AI Model Design'),
      h2('4.1 Algorithm Selection'),
      body('Random Forest Classifier (scikit-learn) was selected for both tasks based on:'),
      bullet('Strong performance on tabular/mixed-type medical data'),
      bullet('Native feature importance for explainability (no post-hoc approximation needed)'),
      bullet('Robustness to outliers and missing values common in clinical records'),
      bullet('Balanced class handling via class_weight="balanced"'),
      bullet('No requirement for normality assumption (unlike logistic regression)'),
      ...spacer(1),
      h2('4.2 Hyperparameters'),
      twoColTable([
        ['Parameter', 'Heart Disease / Symptom-Disease'],
        ['n_estimators', '200 / 300 — more trees for 15-class problem'],
        ['max_depth', '8 / 12 — controlled to reduce overfitting'],
        ['min_samples_split', '10 / 5 — regularization via minimum node split'],
        ['min_samples_leaf', '4 / 2 — smoothing low-frequency nodes'],
        ['class_weight', '"balanced" — handles class imbalance automatically'],
        ['random_state', '42 — reproducibility'],
        ['n_jobs', '-1 — parallel training across all CPU cores'],
      ]),
      ...spacer(1),
      h2('4.3 Cross-Validation'),
      body('5-fold Stratified K-Fold cross-validation was used to estimate generalization performance before final model training:'),
      bullet('Heart Disease: CV AUC-ROC = 0.9238 ± 0.0130'),
      bullet('Symptom-Disease: CV Accuracy = 0.9187 ± 0.0146'),
      body('Low standard deviation confirms stable learning — no significant overfitting.'),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 5 — PERFORMANCE METRICS
      // ══════════════════════════════════════════════════════
      h1('5. Performance Evaluation'),
      h2('5.1 Metrics Summary'),
      metricsTable([
        ['Accuracy', '81.0%', '90.7%', '> 80%'],
        ['Precision', '0.7857', '0.9067', '> 0.75'],
        ['Recall', '0.7944', '0.9067', '> 0.75'],
        ['F1 Score', '0.7901', '0.9067', '> 0.75'],
        ['AUC-ROC', '0.9121', 'N/A (multi-class)', '> 0.85'],
        ['CV Score (mean)', '0.9238 AUC', '0.9187 Acc', '> 0.85'],
        ['CV Score (std)', '±0.013', '±0.015', '< ±0.05'],
      ]),
      ...spacer(1),
      h2('5.2 Explainability Method'),
      body('MedAI implements a lightweight SHAP-compatible local explanation engine using Random Forest feature importances multiplied by input activation values:'),
      ...spacer(1),
      body('contribution(feature_i) = global_importance(feature_i) × |input_value_i|', { font: 'Courier New', size: 20, color: '2C3E50' }),
      ...spacer(1),
      body('Top-N contributing features are displayed in the results UI with relative bar charts, enabling clinicians to understand which symptoms or biomarkers most influenced a given prediction. This satisfies clinical audit requirements for AI-assisted decision support.'),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 6 — SECURITY & COMPLIANCE
      // ══════════════════════════════════════════════════════
      h1('6. Security & HIPAA Compliance'),
      h2('6.1 Implemented Controls'),
      twoColTable([
        ['Control', 'Implementation'],
        ['Authentication', 'werkzeug bcrypt password hashing; session token generation'],
        ['Session Security', 'HTTP-Only cookies; SameSite=Lax; server-side session'],
        ['Rate Limiting', 'Token bucket: 30 req/min per IP; 429 abort on excess'],
        ['Input Sanitization', 'Type-bound range validation; symptom whitelist enforcement'],
        ['Audit Logging', 'JSON audit trail: timestamp, event type, anonymized user hash, hashed IP'],
        ['Data Anonymization', 'User IDs and IPs stored as one-way SHA-256 hashes (16-char prefix)'],
        ['XSS Prevention', 'Jinja2 autoescaping; no raw HTML from user input rendered'],
        ['Content Security', 'MAX_CONTENT_LENGTH = 2 MB; no file upload endpoints'],
      ]),
      ...spacer(1),
      h2('6.2 HIPAA Audit Log Format'),
      code('{"timestamp": "2024-01-15T10:23:45Z",'),
      code(' "event": "SYMPTOM_PREDICTION",'),
      code(' "user": "a3f9c2b1d4e7f012",  // SHA-256 hash (16 char)'),
      code(' "ip": "8b1e4a2f9c3d",         // IP hash'),
      code(' "details": {"num_symptoms": 6, "primary": "Influenza"}}'),
      ...spacer(1),
      h2('6.3 Production Hardening Checklist'),
      bullet('Set SECRET_KEY via environment variable (never hardcoded)'),
      bullet('Enable HTTPS via TLS certificate on load balancer / reverse proxy'),
      bullet('Deploy in VPC private subnet; expose only ALB/NGINX publicly'),
      bullet('Store model artifacts in S3 with server-side encryption (AES-256)'),
      bullet('Enable CloudTrail / Cloud Audit Logs for infrastructure-level auditing'),
      bullet('Apply WAF rules (OWASP Top 10) on edge layer'),
      bullet('Set log retention to minimum 90 days (HIPAA requirement)'),
      bullet('Replace in-memory user store with encrypted database (PostgreSQL/RDS)'),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 7 — DEPLOYMENT
      // ══════════════════════════════════════════════════════
      h1('7. Deployment Guide'),
      h2('7.1 Local Development'),
      numbered('Clone repository and install dependencies:'),
      code('pip install -r requirements.txt'),
      numbered('Generate datasets and train models:'),
      code('python3 data/generate_dataset.py'),
      code('python3 model/train.py'),
      numbered('Start Flask development server:'),
      code('python3 app.py'),
      numbered('Access at http://localhost:5000 — login: doctor / clinic2024'),
      ...spacer(1),
      h2('7.2 Docker (Production)'),
      code('docker build -t medai-diagnostics .'),
      code('docker run -p 8080:8080 \\'),
      code('  -e SECRET_KEY="your-32-char-secret" \\'),
      code('  medai-diagnostics'),
      ...spacer(1),
      h2('7.3 AWS ECS / Fargate'),
      bullet('Push image to AWS ECR (see DEPLOY.sh)'),
      bullet('Create Fargate task definition: 1 vCPU, 2 GB RAM'),
      bullet('Deploy ECS service behind an Application Load Balancer (ALB)'),
      bullet('Attach ACM certificate to ALB for HTTPS termination'),
      bullet('Configure CloudWatch log group with 90-day retention'),
      bullet('Store SECRET_KEY in AWS Secrets Manager; inject via ECS task env'),
      ...spacer(1),
      h2('7.4 Alternative Platforms'),
      twoColTable([
        ['Platform', 'Command'],
        ['Google Cloud Run', 'gcloud run deploy medai --image gcr.io/PROJECT/medai --memory 2Gi'],
        ['Azure Container Apps', 'az containerapp create --name medai --cpu 1 --memory 2Gi'],
        ['Heroku', 'heroku container:push web && heroku container:release web'],
        ['Railway / Render', 'Push Dockerfile; set PORT=8080 env var'],
      ]),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 8 — UI & API
      // ══════════════════════════════════════════════════════
      h1('8. Web Interface & API'),
      h2('8.1 Routes Reference'),
      twoColTable([
        ['Route', 'Description'],
        ['GET /', 'Dashboard — model metrics, recent predictions, module access'],
        ['GET/POST /login', 'Authentication portal'],
        ['GET/POST /diagnose/symptoms', 'Symptom checker form + inference results'],
        ['GET/POST /diagnose/heart', 'Heart disease biomarker form + results'],
        ['GET /metrics', 'Full model performance report with evaluation plots'],
        ['GET /history', 'Session-based prediction history (last 20)'],
        ['GET /api/symptoms', 'JSON list of all valid symptom keys'],
        ['GET /api/metrics', 'JSON model performance metrics'],
      ]),
      ...spacer(1),
      h2('8.2 JSON API Example (Symptom Prediction)'),
      body('For EMR/EHR integration, use the REST API endpoints with session cookie authentication:'),
      code('POST /diagnose/symptoms'),
      code('Content-Type: application/x-www-form-urlencoded'),
      code(''),
      code('symptoms=fever&symptoms=cough&symptoms=fatigue&age=35&gender=Female'),
      ...spacer(1),
      h2('8.3 Design System'),
      body('The frontend uses a dark clinical aesthetic ("Deep Navy + Clinical Red") with:'),
      bullet('Syne display font (headings) + DM Sans body + DM Mono for data'),
      bullet('CSS custom properties for consistent theming and dark mode'),
      bullet('Animated probability bars and fade-in card animations'),
      bullet('Risk badge system: Low / Moderate / High / Critical with color coding'),
      bullet('WCAG 2.1 AA contrast ratios maintained throughout'),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 9 — EXTENSION & ROADMAP
      // ══════════════════════════════════════════════════════
      h1('9. Extension Roadmap'),
      h2('9.1 Immediate Extensions (v1.1)'),
      bullet('Replace synthetic data with real de-identified datasets from MIMIC-III or PhysioNet'),
      bullet('Add SHAP library for true Shapley value explanations (pending pip availability)'),
      bullet('Implement PostgreSQL user database with bcrypt-hashed passwords'),
      bullet('Add PDF report export of diagnosis results'),
      bullet('Two-factor authentication (TOTP) for healthcare professionals'),
      ...spacer(1),
      h2('9.2 Medical Imaging Module (v2.0)'),
      bullet('CNN-based chest X-ray pneumonia classifier (CheXNet architecture)'),
      bullet('Retinal image diabetic retinopathy screening (EfficientNet-B4)'),
      bullet('DICOM viewer integration for direct PACS connection'),
      bullet('Cloud GPU training on AWS SageMaker or Google Vertex AI'),
      ...spacer(1),
      h2('9.3 EHR/EMR Integration (v2.1)'),
      bullet('HL7 FHIR R4 API adapter for bidirectional EHR integration'),
      bullet('Epic / Cerner / Allscripts connector modules'),
      bullet('Automated lab result ingestion and real-time risk alerts'),
      bullet('Multi-tenant architecture with per-hospital data isolation'),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // SECTION 10 — PROJECT FILE STRUCTURE
      // ══════════════════════════════════════════════════════
      h1('10. Project File Structure'),
      twoColTable([
        ['Path', 'Description'],
        ['app.py', 'Flask application — all routes, auth, API endpoints'],
        ['data/generate_dataset.py', 'Synthetic dataset generator (heart disease + symptom-disease)'],
        ['model/train.py', 'Model training pipeline — both classifiers + evaluation plots'],
        ['model/predict.py', 'Inference engine — prediction + explanation functions'],
        ['model/artifacts/', 'Trained .pkl models + JSON metadata'],
        ['utils/security.py', 'Auth, rate limiting, sanitization, audit logging'],
        ['templates/', 'Jinja2 HTML templates (base, login, forms, results, metrics)'],
        ['static/css/style.css', 'Design system — 600+ line CSS with custom properties'],
        ['static/js/app.js', 'Frontend JS — animations, bar growth, range sync'],
        ['static/img/plots/', 'Training evaluation charts (ROC, confusion, importances)'],
        ['tests/test_system.py', 'Comprehensive test suite (model + security + data)'],
        ['Dockerfile', 'Production container definition with Gunicorn'],
        ['requirements.txt', 'Python dependencies'],
        ['DEPLOY.sh', 'AWS/GCP/Azure deployment commands and security checklist'],
        ['logs/audit.log', 'HIPAA audit trail (auto-created on first run)'],
      ]),
      ...spacer(1),
      divider(),

      // ══════════════════════════════════════════════════════
      // DISCLAIMER
      // ══════════════════════════════════════════════════════
      h1('Clinical Disclaimer'),
      new Paragraph({
        spacing: { before: 120, after: 120 },
        shading: { fill: 'FFF8E1', type: ShadingType.CLEAR },
        border: {
          top: { style: BorderStyle.SINGLE, size: 4, color: 'F59E0B', space: 4 },
          bottom: { style: BorderStyle.SINGLE, size: 4, color: 'F59E0B', space: 4 },
          left: { style: BorderStyle.SINGLE, size: 12, color: 'F59E0B', space: 8 },
          right: { style: BorderStyle.NONE },
        },
        children: [
          new TextRun({ text: 'IMPORTANT: ', bold: true, font: 'Arial', size: 22, color: 'D97706' }),
          new TextRun({
            text: 'MedAI is a clinical decision-support tool, not a replacement for professional medical diagnosis. All AI-generated predictions must be reviewed and confirmed by a qualified healthcare professional before any clinical action is taken. The developers and operators of this system disclaim liability for any clinical outcomes arising from use of these predictions without appropriate medical oversight. This system is intended for use by licensed healthcare professionals only.',
            font: 'Arial', size: 22, color: C.black
          })
        ]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/mnt/user-data/outputs/MedAI_Documentation.docx', buffer);
  console.log('Documentation created: MedAI_Documentation.docx');
}).catch(err => {
  console.error(err);
  process.exit(1);
});
