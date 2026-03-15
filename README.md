# AI-Powered Call Quality Analyzer

Hackathon Project — KrenexAI

## Project Overview

An end-to-end AI system that automatically analyzes call center transcripts,
scores agent performance against configurable quality standards (QSDD),
and provides actionable insights through an interactive dashboard.

## Architecture

Raw Data (JSON) -> ETL Pipeline -> DuckDB -> AI Scoring -> ML Models -> Dashboard
                                      |
                                GenAI RAG Agent (LangChain + HuggingFace)

## Project Structure

call_recording_analysis/
├── data/
│   ├── raw/                         Company JSON files
│   └── processed/                   Clean CSVs
├── database/
│   └── call_quality.duckdb          Main database
├── etl/
│   └── etl_pipeline.py              ETL pipeline
├── ml/
│   └── train_models.py              ML model training
├── models/
│   ├── issue_classifier.pkl         Model 1 - Issue Category
│   └── resolution_predictor.pkl     Model 2 - Resolution
├── simulator/
│   └── data_simulator.py            Live data generator
├── tools/
│   ├── qsdd_admin.py                QSDD CRUD
│   ├── db_overview.py               DB inspector
│   └── create_ai_summary_table.py
├── app.py                           Main Streamlit dashboard
├── chat_backend.py                  RAG chatbot backend
├── generate_ai_summary_overwrite_hf.py
├── requirements.txt
└── README.md

## Quick Start

1. Clone repo
   git clone https://github.com/vrajce/call_recording_analysis.git
   cd call_recording_analysis

2. Install dependencies
   pip install -r requirements.txt

3. Initialize database
   python tools/create_ai_summary_table.py

4. Run ETL
   python etl/etl_pipeline.py

5. Train ML models
   python ml/train_models.py

6. Generate AI summaries
   python generate_ai_summary_overwrite_hf.py

7. Launch dashboard
   streamlit run app.py

## What the System Does

| Step        | What                          | Technology                    |
|-------------|-------------------------------|-------------------------------|
| ETL         | Load and clean 45 real calls  | DuckDB + Python               |
| Scoring     | Grade 12 QSDD criteria        | NLP + Sentiment Analysis      |
| ML Model 1  | Auto-tag issue category       | Logistic Regression + TF-IDF  |
| ML Model 2  | Predict call resolution       | Gradient Boosting             |
| GenAI       | Summarize calls + RAG chat    | HuggingFace flan-t5 + LangChain|
| Dashboard   | Visual analytics              | Streamlit + Plotly            |
| Simulator   | Live new calls every 60s      | Python scheduler              |

## Database Tables

| Table              | Rows  | Purpose                          |
|--------------------|-------|----------------------------------|
| calls              | 60+   | Call metadata                    |
| transcripts        | 60+   | Full conversation text           |
| agents             | 28    | Agent profiles                   |
| quality_scores     | 720+  | Per-criteria scores              |
| call_summary       | 60+   | Overall scores and summaries     |
| qsdd_framework     | 12    | Configurable quality rules       |
| data_quality_log   | 4+    | ETL issues found                 |
| ai_summary         | 60+   | HuggingFace generated summaries  |

## Results

- 60+ calls analyzed (45 real + 15 simulated)
- 720+ quality scores across 12 QSDD criteria
- 4 issue categories auto-classified
- 3 resolution outcomes predicted
- RAG chatbot answers manager questions in plain English

## Team Division

Your Name   : Data Engineering, ETL, ML Models, Quality Scoring, Simulator
Friend Name : GenAI RAG Agent, AI Summaries, QSDD Admin UI, Streamlit App
