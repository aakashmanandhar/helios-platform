from rest_framework.decorators import api_view
from rest_framework.response import Response
from helios_dashboard.bq_client import run_query


@api_view(["GET"])
def ltv_rfm(request):
    segments = run_query("""
        SELECT
            rfm_segment,
            COUNT(*) AS customer_count,
            ROUND(AVG(lifetime_value), 2) AS avg_ltv,
            ROUND(SUM(lifetime_value), 2) AS total_ltv
        FROM `gold.mart_customer_ltv_rfm`
        GROUP BY rfm_segment
        ORDER BY total_ltv DESC
    """)
    top_customers = run_query("""
        SELECT customer_id, first_name, last_name, region, lifetime_value, rfm_segment
        FROM `gold.mart_customer_ltv_rfm`
        ORDER BY lifetime_value DESC
        LIMIT 10
    """)
    return Response({"segments": segments, "top_customers": top_customers})


@api_view(["GET"])
def churn_risk(request):
    at_risk_summary = run_query("""
        SELECT
            rfm_segment,
            COUNT(*) AS customer_count,
            ROUND(AVG(recency_days), 1) AS avg_recency_days
        FROM `gold.mart_customer_ltv_rfm`
        WHERE rfm_segment IN ('At Risk', 'Lost', 'Needs Attention')
        GROUP BY rfm_segment
        ORDER BY customer_count DESC
    """)
    recency_buckets = run_query("""
        SELECT
            CASE
                WHEN recency_days <= 30 THEN '0-30 days'
                WHEN recency_days <= 60 THEN '31-60 days'
                WHEN recency_days <= 90 THEN '61-90 days'
                WHEN recency_days <= 180 THEN '91-180 days'
                ELSE '180+ days'
            END AS recency_bucket,
            COUNT(*) AS customer_count
        FROM `gold.mart_customer_ltv_rfm`
        GROUP BY recency_bucket
        ORDER BY MIN(recency_days)
    """)
    return Response({"at_risk_summary": at_risk_summary, "recency_buckets": recency_buckets})


@api_view(["GET"])
def marketing_roi(request):
    by_channel = run_query("""
        SELECT
            channel_code,
            ROUND(SUM(spend), 2) AS total_spend,
            ROUND(SUM(revenue), 2) AS total_revenue,
            SUM(orders) AS total_orders,
            ROUND(SAFE_DIVIDE(SUM(revenue), SUM(spend)), 2) AS roas,
            ROUND(SAFE_DIVIDE(SUM(spend), SUM(orders)), 2) AS cac
        FROM `gold.mart_marketing_roi`
        GROUP BY channel_code
        ORDER BY total_spend DESC
    """)
    monthly_trend = run_query("""
        SELECT
            DATE_TRUNC(date_day, MONTH) AS month,
            channel_code,
            ROUND(SUM(spend), 2) AS spend,
            ROUND(SUM(revenue), 2) AS revenue
        FROM `gold.mart_marketing_roi`
        GROUP BY month, channel_code
        ORDER BY month
    """)
    return Response({"by_channel": by_channel, "monthly_trend": monthly_trend})


@api_view(["GET"])
def funnel_conversion(request):
    by_channel = run_query("""
        SELECT
            channel_code,
            SUM(sessions) AS sessions,
            SUM(viewed_sessions) AS viewed_sessions,
            SUM(carted_sessions) AS carted_sessions,
            SUM(checkout_sessions) AS checkout_sessions,
            SUM(purchase_sessions) AS purchase_sessions,
            ROUND(SAFE_DIVIDE(SUM(purchase_sessions), SUM(sessions)) * 100, 2) AS overall_conversion_pct
        FROM `gold.mart_funnel_conversion`
        GROUP BY channel_code
        ORDER BY sessions DESC
    """)
    overall = run_query("""
        SELECT
            SUM(sessions) AS sessions,
            SUM(viewed_sessions) AS viewed_sessions,
            SUM(carted_sessions) AS carted_sessions,
            SUM(checkout_sessions) AS checkout_sessions,
            SUM(purchase_sessions) AS purchase_sessions,
            ROUND(SAFE_DIVIDE(SUM(carted_sessions), SUM(viewed_sessions)) * 100, 2) AS view_to_cart_pct,
            ROUND(SAFE_DIVIDE(SUM(checkout_sessions), SUM(carted_sessions)) * 100, 2) AS cart_to_checkout_pct,
            ROUND(SAFE_DIVIDE(SUM(purchase_sessions), SUM(checkout_sessions)) * 100, 2) AS checkout_to_purchase_pct
        FROM `gold.mart_funnel_conversion`
    """)
    return Response({"overall": overall[0] if overall else {}, "by_channel": by_channel})


@api_view(["GET"])
def inventory_risk(request):
    status_summary = run_query("""
        SELECT
            inventory_status,
            COUNT(*) AS product_count,
            ROUND(SUM(inventory_value_at_cost), 2) AS total_value
        FROM `gold.mart_inventory_risk`
        GROUP BY inventory_status
        ORDER BY total_value DESC
    """)
    by_warehouse = run_query("""
        SELECT
            warehouse_code,
            warehouse_name,
            region,
            COUNTIF(is_stockout) AS stockout_count,
            COUNTIF(is_overstock) AS overstock_count,
            ROUND(SUM(inventory_value_at_cost), 2) AS total_value
        FROM `gold.mart_inventory_risk`
        GROUP BY warehouse_code, warehouse_name, region
        ORDER BY warehouse_code
    """)
    return Response({"status_summary": status_summary, "by_warehouse": by_warehouse})
