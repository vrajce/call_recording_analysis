
# ml/train_models.py
# Run: python ml/train_models.py
import joblib, duckdb, os
import pandas as pd
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
import warnings
warnings.filterwarnings("ignore")

DB_PATH    = "database/call_quality.duckdb"
MODEL_PATH = "models"
os.makedirs(MODEL_PATH, exist_ok=True)

def train_all():
    con = duckdb.connect(DB_PATH)
    df  = con.execute("""
        SELECT t.contact_id, t.agent_text, t.customer_text,
               t.agent_word_count, t.customer_word_count, t.talk_ratio,
               c.campaign_name, c.total_duration_sec, c.agent_seconds,
               c.in_queue_seconds, c.hold_seconds, c.hold_count,
               c.acw_seconds, c.is_abandoned, c.is_outbound,
               c.service_level_flag, c.is_simulated,
               cs.overall_score, cs.sentiment_agent, cs.sentiment_customer,
               cs.issue_category, cs.resolution
        FROM transcripts t
        JOIN calls c         ON t.contact_id = c.contact_id
        JOIN call_summary cs ON t.contact_id = cs.contact_id
    """).fetchdf()
    con.close()

    print(f"Training on {len(df)} total calls")

    # Model 1 — Issue Classifier
    df["customer_text"] = df["customer_text"].fillna("")
    df["agent_text"]    = df["agent_text"].fillna("")
    df["campaign_name"] = df["campaign_name"].fillna("Unknown")
    combined = df["customer_text"] + " " + df["agent_text"]

    tfidf  = TfidfVectorizer(max_features=300, ngram_range=(1,2),
                              stop_words="english", sublinear_tf=True)
    X_text = tfidf.fit_transform(combined)
    NUM_M1 = ["total_duration_sec","agent_word_count","customer_word_count",
              "talk_ratio","overall_score","hold_count","hold_seconds","in_queue_seconds"]
    X_num  = csr_matrix(df[NUM_M1].fillna(0).values)
    ohe    = OneHotEncoder(sparse_output=True, handle_unknown="ignore")
    X_cat  = ohe.fit_transform(df[["campaign_name"]])
    X_m1   = hstack([X_text, X_num, X_cat])
    le_m1  = LabelEncoder()
    y_m1   = le_m1.fit_transform(df["issue_category"])

    model1 = LogisticRegression(max_iter=1000, C=1.0,
                                 class_weight="balanced", random_state=42)
    model1.fit(X_m1, y_m1)
    joblib.dump({"model":model1,"tfidf":tfidf,"ohe":ohe,"label_encoder":le_m1,
                 "model_name":"Logistic Regression","classes":list(le_m1.classes_),
                 "num_cols":NUM_M1,"trained_on":len(df)},
                f"{MODEL_PATH}/issue_classifier.pkl")
    print(f"Model 1 saved — classes: {list(le_m1.classes_)}")

    # Model 2 — Resolution Predictor
    df2 = df[df["resolution"] != "Abandoned"].copy()
    sm  = {"Positive":2,"Neutral":1,"Negative":0}
    df2["sentiment_agent_num"]    = df2["sentiment_agent"].map(sm).fillna(1)
    df2["sentiment_customer_num"] = df2["sentiment_customer"].map(sm).fillna(1)
    df2["sla_met"]   = (df2["service_level_flag"]=="1").astype(int)
    im = {"Technical Issue":0,"Account Access":1,"Billing":2,"Software Request":3}
    df2["issue_num"] = df2["issue_category"].map(im).fillna(0)
    NUM_M2 = ["total_duration_sec","agent_seconds","acw_seconds",
              "in_queue_seconds","hold_seconds","hold_count",
              "agent_word_count","customer_word_count","talk_ratio",
              "overall_score","sentiment_agent_num","sentiment_customer_num",
              "sla_met","issue_num","is_abandoned","is_outbound"]
    scaler  = StandardScaler()
    X_m2_sc = scaler.fit_transform(df2[NUM_M2].fillna(0).astype(float).values)
    le_m2   = LabelEncoder()
    y_m2    = le_m2.fit_transform(df2["resolution"])
    model2  = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                          learning_rate=0.1, random_state=42)
    model2.fit(X_m2_sc, y_m2)
    joblib.dump({"model":model2,"scaler":scaler,"label_encoder":le_m2,
                 "model_name":"Gradient Boosting","classes":list(le_m2.classes_),
                 "feature_cols":NUM_M2,"num_cols":NUM_M2,"trained_on":len(df2)},
                f"{MODEL_PATH}/resolution_predictor.pkl")
    print(f"Model 2 saved — classes: {list(le_m2.classes_)}")

if __name__ == "__main__":
    train_all()
