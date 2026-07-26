import json
import random
import time
import uuid
from datetime import datetime, timezone
from confluent_kafka import Producer

BOOTSTRAP_SERVERS = "localhost:19092"
TOPIC = "clickstream_events"

N_CUSTOMERS = 200_000
N_PRODUCTS = 8_000
DURATION_SECONDS = 60
TARGET_EVENTS_PER_SEC = 50

CHANNELS = ["organic", "paid_search", "direct", "email", "affiliate"]
CHANNEL_WEIGHTS = [0.35, 0.25, 0.20, 0.12, 0.08]

producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")

def emit(event):
    producer.produce(TOPIC, key=event["session_id"], value=json.dumps(event), callback=delivery_report)

def simulate_session():
    session_id = str(uuid.uuid4())
    customer_id = random.randint(1, N_CUSTOMERS)
    channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
    viewed_products = random.sample(range(1, N_PRODUCTS + 1), k=random.randint(1, 5))
    now = datetime.now(timezone.utc)
    events = []

    for product_id in viewed_products:
        events.append({
            "event_id": str(uuid.uuid4()), "session_id": session_id, "customer_id": customer_id,
            "product_id": product_id, "event_type": "page_view", "channel": channel,
            "event_timestamp": now.isoformat(),
        })

    if random.random() < 0.30:
        cart_product = random.choice(viewed_products)
        events.append({
            "event_id": str(uuid.uuid4()), "session_id": session_id, "customer_id": customer_id,
            "product_id": cart_product, "event_type": "add_to_cart", "channel": channel,
            "event_timestamp": now.isoformat(),
        })
        if random.random() < 0.50:
            events.append({
                "event_id": str(uuid.uuid4()), "session_id": session_id, "customer_id": customer_id,
                "product_id": cart_product, "event_type": "checkout_start", "channel": channel,
                "event_timestamp": now.isoformat(),
            })
            if random.random() < 0.70:
                events.append({
                    "event_id": str(uuid.uuid4()), "session_id": session_id, "customer_id": customer_id,
                    "product_id": cart_product, "event_type": "purchase", "channel": channel,
                    "event_timestamp": now.isoformat(),
                })
    return events

if __name__ == "__main__":
    print(f"Producing clickstream events for {DURATION_SECONDS}s...")
    start = time.time()
    total_events, total_sessions = 0, 0
    while time.time() - start < DURATION_SECONDS:
        events = simulate_session()
        for e in events:
            emit(e)
            total_events += 1
        total_sessions += 1
        producer.poll(0)
        time.sleep(len(events) / TARGET_EVENTS_PER_SEC)

    producer.flush()
    print(f"Done. {total_sessions} sessions, {total_events} events produced in {time.time()-start:.1f}s.")
