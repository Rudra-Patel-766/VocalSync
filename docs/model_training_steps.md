# Emotion Model Training Steps

This guide trains a lightweight text emotion model for post-session analysis while keeping realtime websocket feedback fast.

## 1. Prepare dataset

Use a CSV with at least 50 rows and two columns:
- text
- label

Example labels: confident, nervous, excited, calm, neutral.

## 2. Install backend requirements

Run in backend folder:

```powershell
C:/Users/shukl/OneDrive/Desktop/ai_doc/speech-coach-ai/backend/venv/Scripts/python.exe -m pip install -r requirements.txt
```

## 3. Train model

```powershell
C:/Users/shukl/OneDrive/Desktop/ai_doc/speech-coach-ai/backend/venv/Scripts/python.exe ml/train_emotion_model.py --dataset path/to/emotion_dataset.csv --text-column text --label-column label --model-version v1
```

## 4. Generated artifacts

After training, artifacts are saved in backend/ml/artifacts:
- emotion_text_pipeline.joblib
- emotion_model_meta.json
- emotion_train_metrics.json

## 5. Verify effectiveness metrics

Open emotion_train_metrics.json and report:
- preprocessing.raw_rows
- preprocessing.usable_rows
- preprocessing dropped counts
- training.feature_selection.tfidf_feature_count
- training.feature_selection.selected_feature_count
- training.accuracy
- training.macro_f1
- training.classification_report

## 6. Runtime behavior

If artifacts exist, backend uses model inference for emotion label in complete-session analysis.
If artifacts are missing, backend automatically falls back to rule-based emotion detection.
