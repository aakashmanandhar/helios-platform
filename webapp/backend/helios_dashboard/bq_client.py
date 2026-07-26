from functools import lru_cache
from django.conf import settings
from google.cloud import bigquery


@lru_cache(maxsize=1)
def get_bq_client():
    return bigquery.Client(project=settings.GCP_PROJECT_ID)


def run_query(sql):
    client = get_bq_client()
    return [dict(row) for row in client.query(sql).result()]
