import os
import json
import time
import psycopg2
from kafka import KafkaConsumer

# Load environment configuration with strict fallbacks
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transaction-signals")
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgres://postgres:postgres@localhost:5432/postgres"
)

def get_supabase_connection():
    """
    Establishes a resilient connection to the Supabase PostgreSQL database instances.
    """
    try:
        connection = psycopg2.connect(DATABASE_URL)
        return connection
    except Exception as db_err:
        print(f"[FATAL] Unable to connect to Supabase database: {db_err}")
        return None

def mock_ai_classification_engine(raw_text: str) -> tuple:
    """
    A deterministic fallback modeling engine. Mimics NLP extraction 
    by mapping messy enterprise text into clean names and precise industries.
    """
    text_lower = raw_text.lower()
    
    if "aws" in text_lower or "amazon_mktpl" in text_lower:
        return "Amazon Web Services", "Cloud Infrastructure"
    elif "vndr_supply" in text_lower or "chai" in text_lower:
        return "Local Grocery & Supplies", "Office Operations"
    elif "uber" in text_lower or "lyft" in text_lower:
        return "Rideshare Transport", "Travel & Logistics"
    elif "github" in text_lower or "cursor" in text_lower:
        return "Developer Tooling Suite", "Software Subscriptions"
    else:
        return "Unclassified Merchant Asset", "General Operating Expense"

def process_transaction_event(event_data):
    """
    Processes a single transaction message: performs AI cleanup and updates Supabase.
    """
    tx_id = event_data.get("transaction_id")
    raw_text = event_data.get("raw_text")

    if not tx_id or not raw_text:
        print("[ERROR] Received malformed Kafka event payload skipping record.")
        return

    print(f"[PROCESSING] Ingesting Transaction ID: {tx_id} | Raw Input: '{raw_text}'")

    # Pass the messy bank statement string through our AI classification mechanism
    clean_name, category = mock_ai_classification_engine(raw_text)

    # Establish connection to write back results
    conn = get_supabase_connection()
    if not conn:
        print(f"[RETRY_DELAY] Postponing event processing due to database unavailability for ID: {tx_id}")
        return

    try:
        cursor = conn.cursor()
        
        # SQL Statement to enrich our pending transaction record and mark it PROCESSED
        update_query = """
            UPDATE transactions
            SET clean_name = %s,
                category = %s,
                status = 'PROCESSED'
            WHERE id = %s;
        """
        
        cursor.execute(update_query, (clean_name, category, tx_id))
        conn.commit()
        cursor.close()
        print(f"[SUCCESS] Successfully cleaned and committed ID: {tx_id} as [{clean_name}] under [{category}]")
        
    except Exception as sql_err:
        conn.rollback()
        print(f"[ERROR] Database write transaction failed for ID {tx_id}: {sql_err}")
    finally:
        conn.close()

def main():
    """
    Main background runner executing a continuous event ingestion loop from Kafka.
    """
    print(f"Starting Python MLOps Background Worker Plane...")
    print(f"Connecting to Kafka Broker at: {KAFKA_BROKER} on Topic: {KAFKA_TOPIC}")

    # Initialize a reliable, persistent Kafka Consumer instance
    consumer = None
    retry_attempts = 0
    
    while not consumer:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                group_id='mlops-inference-worker-group', # Enforces cooperative message balancing across workers
                auto_offset_reset='earliest',             # Automatically processes old historical events if workers go offline
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
        except Exception as kafka_err:
            retry_attempts += 1
            print(f"[WARNING] Kafka Broker not reachable yet. Retry attempt #{retry_attempts} in 5 seconds...")
            time.sleep(5)

    print("[READY] Worker fully connected to Kafka pipeline. Monitoring incoming streams...")

    # Continuous stream loop execution blocks until interrupted safely
    try:
        for message in consumer:
            event_data = message.value
            process_transaction_event(event_data)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Terminating worker loop cleanly.")
    finally:
        if consumer:
            consumer.close()
        print("[OFFLINE] Python background worker offline.")

if __name__ == "__main__":
    main()