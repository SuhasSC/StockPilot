import re


def generate_aggregation_query(question: str):
    """Return an aggregation plan for supported analytical questions."""
    text = question.lower().strip()

    # Monthly revenue from completed sales. sale_date is stored as YYYY-MM-DD.
    if any(term in text for term in [
        "monthly revenue", "revenue by month", "revenue per month",
        "sales by month", "month-wise sales", "monthly sales",
    ]):
        return {
            "query_type": "aggregate",
            "collection": "sales",
            "pipeline": [
                {"$match": {"status": "completed"}},
                {
                    "$group": {
                        "_id": {"$substrCP": ["$sale_date", 0, 7]},
                        "total_revenue": {"$sum": "$total_amount"},
                        "sales_count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
                {"$limit": 100},
            ],
            "description": "Calculate completed-sales revenue for each month",
        }

    # Sales or revenue grouped by city.
    if any(term in text for term in [
        "sales by city", "revenue by city", "city-wise sales",
        "city wise sales", "sales in each city", "sales per city",
    ]):
        return {
            "query_type": "aggregate",
            "collection": "sales",
            "pipeline": [
                {"$match": {"status": "completed"}},
                {
                    "$group": {
                        "_id": "$city",
                        "total_revenue": {"$sum": "$total_amount"},
                        "units_sold": {"$sum": "$quantity"},
                        "sales_count": {"$sum": 1},
                    }
                },
                {"$sort": {"total_revenue": -1, "_id": 1}},
                {"$limit": 100},
            ],
            "description": "Summarize completed sales by city",
        }

    # Count inventory items at or below reorder level.
    if (
        any(term in text for term in [
            "low stock count", "count low stock", "how many low stock",
            "number of low stock", "low stock items count",
            "count items below reorder", "how many items need restocking",
        ])
    ):
        return {
            "query_type": "aggregate",
            "collection": "inventory",
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$lte": ["$stock_quantity", "$reorder_level"]
                        }
                    }
                },
                {"$group": {"_id": None, "low_stock_count": {"$sum": 1}}},
            ],
            "description": "Count inventory records at or below reorder level",
        }

    # Category summary: product count and average price per category.
    if any(term in text for term in [
        "category summary", "category summaries", "summary by category",
        "products by category", "category-wise products",
        "category wise products", "summarize categories",
    ]):
        return {
            "query_type": "aggregate",
            "collection": "products",
            "pipeline": [
                {
                    "$group": {
                        "_id": "$category",
                        "product_count": {"$sum": 1},
                        "average_price": {"$avg": "$price"},
                    }
                },
                {"$sort": {"product_count": -1, "_id": 1}},
                {"$limit": 100},
            ],
            "description": "Summarize product counts and average prices by category",
        }

    # Best-selling products by units sold.
    if any(term in text for term in [
        "sold the most", "best-selling", "best selling", "bestselling",
        "top selling", "top-selling", "highest selling",
        "most units sold",
    ]):
        limit_match = re.search(r"\btop\s+(\d{1,2})\b", text)
        limit = min(int(limit_match.group(1)), 20) if limit_match else 5

        return {
            "query_type": "aggregate",
            "collection": "sales",
            "pipeline": [
                {
                    "$group": {
                        "_id": "$product_id",
                        "product_name": {"$first": "$product_name"},
                        "units_sold": {"$sum": "$quantity"},
                    }
                },
                {"$sort": {"units_sold": -1, "_id": 1}},
                {"$limit": limit},
            ],
            "description": f"Rank the top {limit} products by total units sold",
        }

    # Total revenue across completed sales.
    if any(term in text for term in [
        "total sales revenue", "total revenue",
        "total sales amount", "revenue generated",
        "how much revenue",
    ]):
        return {
            "query_type": "aggregate",
            "collection": "sales",
            "pipeline": [
                {"$match": {"status": "completed"}},
                {
                    "$group": {
                        "_id": None,
                        "total_revenue": {"$sum": "$total_amount"},
                    }
                },
            ],
            "description": "Calculate total revenue from completed sales",
        }

    # Count distinct active supplier companies, not branch records.
    if (
        "supplier" in text
        and "active" in text
        and (
            any(term in text for term in [
                "how many", "count", "number of", "total",
            ])
            or any(term in text for term in [
                "show active suppliers", "list active suppliers",
                "active supplier companies",
            ])
        )
    ):
        return {
            "query_type": "aggregate",
            "collection": "suppliers",
            "pipeline": [
                {"$match": {"status": "active"}},
                {"$group": {"_id": "$supplier_id"}},
                {"$group": {"_id": None, "active_supplier_companies": {"$sum": 1}}},
            ],
            "description": "Count distinct active supplier companies",
        }

    # Count completed sales records.
    if any(term in text for term in [
        "completed sales count", "count completed sales",
        "number of completed sales", "how many completed sales",
    ]):
        return {
            "query_type": "aggregate",
            "collection": "sales",
            "pipeline": [
                {"$match": {"status": "completed"}},
                {"$group": {"_id": None, "completed_sales_count": {"$sum": 1}}},
            ],
            "description": "Count completed sales records",
        }

    # Average product price.
    if any(term in text for term in [
        "average product price", "average price",
        "mean product price",
    ]):
        return {
            "query_type": "aggregate",
            "collection": "products",
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "average_price": {"$avg": "$price"},
                    }
                },
            ],
            "description": "Calculate the average product price",
        }

    return None
