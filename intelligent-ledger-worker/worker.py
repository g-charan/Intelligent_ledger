import os
import json
import time
import psycopg2
from kafka import KafkaConsumer
import joblib

# Environment
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transaction-signals")
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/postgres")


class HighPowerAIEngine:
    """
    Lightweight local inference engine. Loads a Joblib-serialized scikit-learn
    pipeline if present; otherwise falls back to simple rule-based heuristics.
    """

    def __init__(self, model_path="model.joblib"):
        self.model_path = model_path
        self.model = None
        self.load_model_artifact()

    def load_model_artifact(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"[AI ENGINE] Loaded model artifact: {self.model_path}")
            else:
                print(f"[AI ENGINE] Model artifact not found at {self.model_path}; using fallback rules")
        except Exception as err:
            print(f"[AI ENGINE ERROR] Failed loading model artifact: {err}")
            self.model = None

    def predict_merchant_details(self, raw_text: str):
        # If a model is available, try to use it. Support models that return
        # a single label or a tuple/list (clean_name, category).
        if self.model is not None:
            try:
                pred = self.model.predict([raw_text])[0]
                if isinstance(pred, (list, tuple)) and len(pred) >= 2:
                    return str(pred[0]), str(pred[1])
                return str(pred), "Unclassified"
            except Exception as e:
                print(f"[AI INFERENCE ERROR] Model inference failed: {e}")

        # Fallback simple rules
        text_lower = (raw_text or "").lower()
        if "aws" in text_lower or "amazon" in text_lower:
            return "Amazon Web Services", "Cloud Infrastructure"
        if "github" in text_lower or "cursor" in text_lower:
            return "Developer Tooling Suite", "Software Subscriptions"
        if "uber" in text_lower or "lyft" in text_lower:
            return "Rideshare Transport", "Travel & Logistics"
        return "Unclassified Merchant Asset", "General Operating Expense"


def get_supabase_connection():
    if not DATABASE_URL:
        print("[DATABASE] DATABASE_URL not set in environment")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as db_err:
        print(f"[DATABASE HANDSHAKE ERROR] {db_err}")
        return None


def process_transaction_event(event_data, ai_engine: HighPowerAIEngine):
    tx_id = event_data.get("transaction_id") or event_data.get("id")
    raw_text = event_data.get("raw_text")
    if not tx_id or not raw_text:
        print("[PROCESS] Invalid event; missing id or raw_text")
        return

    print(f"[PROCESSING] {tx_id} -> {raw_text}")
    clean_name, category = ai_engine.predict_merchant_details(raw_text)

    conn = get_supabase_connection()
    if not conn:
        print("[PROCESS] Could not obtain DB connection; skipping update")
        return

    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE transactions
            SET clean_name = %s,
                category = %s,
                status = 'PROCESSED'
            WHERE id = %s;
            """,
            (clean_name, category, tx_id),
        )
        conn.commit()
        cur.close()
        print(f"[SUCCESS] Enriched {tx_id} -> {clean_name} / {category}")
    except Exception as sql_err:
        conn.rollback()
        print(f"[PERSISTENCE ERROR] {sql_err}")
    finally:
        conn.close()


def main():
    print("Starting worker...")
    ai_engine = HighPowerAIEngine(model_path="model.joblib")

    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                group_id="mlops-inference-worker-group",
                auto_offset_reset="earliest",
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            )
        except Exception as e:
            print(f"[KAFKA] Consumer connect failed, retrying in 2s: {e}")
            time.sleep(2)

    print("[READY] Worker synced with Kafka; listening for messages...")
    try:
        message_count = 0
        for message in consumer:
            message_count += 1
            print(f"[KAFKA MESSAGE RECEIVED] #{message_count}: {message.value}")
            try:
                process_transaction_event(message.value, ai_engine)
            except Exception as e:
                print(f"[WORKER ERROR] Processing message failed: {e}")
    except KeyboardInterrupt:
        print("Shutting down worker")
    finally:
        try:
            consumer.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()