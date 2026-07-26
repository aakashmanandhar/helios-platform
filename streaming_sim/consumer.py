import json
import os
import time
import pandas as pd
from datetime import datetime, timezone
from confluent_kafka import Consumer

BOOTSTRAP_SERVERS = "localhost:19092"
TOPIC = "clickstream_events"
GROUP_ID = "bronze-loader"
BRONZE_ROOT = os.path.join(os.path.dirname(__file__), "..", "lake", "bronze", "clickstream_events")
POLL_TIMEOUT_SECONDS = 10
BATCH_SIZE = 5000

consumer = Consumer({
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "group.id": GROUP_ID,
    "auto.offset.reset": "earliest",
})
consumer.subscribe([TOPIC])

def write_batch(records, batch_num):
    if not records:
        return
    ingested_date = datetime.now(timezone.utc).date().isoformat()
    out_dir = os.path.join(BRONZE_ROOT, f"ingested_date={ingested_date}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"part-{batch_num}-{int(time.time())}.parquet")
    df = pd.DataFrame(records)
    df.to_parquet(out_path, index=False)
    print(f"Wrote {len(records)} events -> {out_path}")

if __name__ == "__main__":
    records = []
    batch_num = 0
    last_message_time = time.time()
    drained = False
    print("Consuming clickstream events...")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                if time.time() - last_message_time > POLL_TIMEOUT_SECONDS:
                    write_batch(records, batch_num)
                    records = []
                    drained = True
                    print("No new messages, stream appears drained. Exiting.")
                    break
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            last_message_time = time.time()
            event = json.loads(msg.value())
            records.append(event)
            if len(records) >= BATCH_SIZE:
                write_batch(records, batch_num)
                batch_num += 1
                records = []
    except KeyboardInterrupt:
        pass
    finally:
        if not drained and records:
            write_batch(records, batch_num)
        consumer.close()
        print("Consumer closed.")
