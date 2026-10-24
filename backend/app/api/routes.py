from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from app.database.mongodb import database
from app.services.query_generator import generate_query
from app.services.llm_query_generator import generate_llm_query
from app.services.category_normalizer import normalize_category
from app.services.semantic_search import SemanticSearch
from app.services.aggregation_generator import generate_aggregation_query
from app.services.query_normalizer import normalize_question
from app.services.question_scope import question_scope_error

router = APIRouter()

COLLECTION_FIELDS = {
    "products": {
        "product_id", "name", "category", "price",
        "description", "supplier_id", "created_date",
    },
    "inventory": {
        "product_id", "warehouse_id", "stock_quantity",
        "reorder_level", "location", "last_updated",
    },
    "sales": {
        "sale_id", "product_id", "product_name", "quantity",
        "unit_price", "total_amount", "sale_date", "city", "status",
    },
    "suppliers": {
        "supplier_record_id", "supplier_id", "name", "branch_id",
        "category_focus", "city", "state", "country", "email",
        "phone", "status", "created_date",
    },
}

ALLOWED_COLLECTIONS = set(COLLECTION_FIELDS)
MIN_SIMILARITY = 0.35

ALLOWED_OPERATORS = {
    "$eq", "$ne", "$gt", "$gte", "$lt", "$lte",
    "$in", "$nin", "$and", "$or", "$expr",
}


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@lru_cache(maxsize=1)
def get_semantic_search():
    return SemanticSearch()


def validate_filter(value, allowed_fields, inside_expr=False):
    """Validate MongoDB filters against the selected collection schema."""
    if isinstance(value, dict):
        for key, child in value.items():
            if inside_expr:
                if key.startswith("$") and key not in ALLOWED_OPERATORS:
                    raise ValueError(f"Disallowed expression operator: {key}")
                validate_filter(child, allowed_fields, inside_expr=True)
            elif key.startswith("$"):
                if key not in ALLOWED_OPERATORS:
                    raise ValueError(f"Disallowed operator: {key}")
                if key == "$expr":
                    if "stock_quantity" not in allowed_fields or "reorder_level" not in allowed_fields:
                        raise ValueError("$expr is only supported for inventory filters.")
                    validate_filter(child, allowed_fields, inside_expr=True)
                else:
                    validate_filter(child, allowed_fields, inside_expr=False)
            else:
                if key not in allowed_fields:
                    raise ValueError(f"Disallowed field: {key}")
                validate_filter(child, allowed_fields, inside_expr=False)

    elif isinstance(value, list):
        for item in value:
            validate_filter(item, allowed_fields, inside_expr=inside_expr)

    elif isinstance(value, str) and inside_expr and value.startswith("$"):
        if value[1:] not in allowed_fields:
            raise ValueError("Disallowed expression field reference.")
    elif not isinstance(value, (str, int, float, bool)) and value is not None:
        raise ValueError("Unsupported query value.")



def validate_aggregation_pipeline(pipeline, collection_name):
    """Allow only the aggregation stages and fields used by our planner."""
    if not isinstance(pipeline, list) or not pipeline or len(pipeline) > 5:
        raise ValueError("Invalid aggregation pipeline.")

    allowed_stages = {"$match", "$group", "$sort", "$limit"}
    allowed_accumulators = {"$sum", "$avg", "$first"}
    allowed_fields = COLLECTION_FIELDS[collection_name]

    for stage in pipeline:
        if not isinstance(stage, dict) or len(stage) != 1:
            raise ValueError("Invalid aggregation stage.")

        stage_name, body = next(iter(stage.items()))
        if stage_name not in allowed_stages:
            raise ValueError("Unsupported aggregation stage.")

        if stage_name == "$match":
            if not isinstance(body, dict):
                raise ValueError("Invalid match stage.")
            validate_filter(body, allowed_fields)

        elif stage_name == "$group":
            if not isinstance(body, dict) or "_id" not in body:
                raise ValueError("Invalid group stage.")

            group_id = body["_id"]
            if isinstance(group_id, str) and group_id.startswith("$"):
                if group_id[1:] not in allowed_fields:
                    raise ValueError("Unsupported group field.")
            elif isinstance(group_id, dict):
                # Only allow the exact month extraction expression used by
                # the trusted monthly-revenue planner.
                if set(group_id) != {"$substrCP"}:
                    raise ValueError("Unsupported group identifier.")

                args = group_id["$substrCP"]
                if (
                    collection_name != "sales"
                    or not isinstance(args, list)
                    or len(args) != 3
                    or args[0] != "$sale_date"
                    or args[1] != 0
                    or args[2] != 7
                    or "sale_date" not in allowed_fields
                ):
                    raise ValueError("Unsupported month grouping expression.")
            elif group_id is not None:
                raise ValueError("Unsupported group identifier.")

            for output_name, expression in body.items():
                if output_name == "_id":
                    continue
                if not isinstance(expression, dict) or len(expression) != 1:
                    raise ValueError("Invalid aggregation expression.")

                operator, operand = next(iter(expression.items()))
                if operator not in allowed_accumulators:
                    raise ValueError("Unsupported aggregation operator.")

                if isinstance(operand, str) and operand.startswith("$"):
                    if operand[1:] not in allowed_fields:
                        raise ValueError("Unsupported aggregation field.")
                elif not isinstance(operand, (int, float)):
                    raise ValueError("Unsupported aggregation value.")

        elif stage_name == "$sort":
            if not isinstance(body, dict) or not body:
                raise ValueError("Invalid sort stage.")
            # Sort may use fields created by the preceding group stage.
            for field_name, direction in body.items():
                if field_name.startswith("$") or direction not in (-1, 1):
                    raise ValueError("Unsupported sort specification.")

        elif stage_name == "$limit":
            if not isinstance(body, int) or isinstance(body, bool) or not 1 <= body <= 100:
                raise ValueError("Invalid aggregation limit.")


def normalize_category_filter(value):
    """Map recognized category values to canonical database values."""
    if isinstance(value, dict):
        normalized = {}
        for key, child in value.items():
            if key == "category":
                if isinstance(child, str):
                    child = normalize_category(child)
                elif isinstance(child, dict):
                    child = {
                        op: (
                            normalize_category(item)
                            if op == "$eq" and isinstance(item, str)
                            else [normalize_category(v) for v in item]
                            if op == "$in" and isinstance(item, list)
                            else item
                        )
                        for op, item in child.items()
                    }
            else:
                child = normalize_category_filter(child)
            normalized[key] = child
        return normalized
    if isinstance(value, list):
        return [normalize_category_filter(item) for item in value]
    return value


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "LLM NoSQL Inventory Management API",
    }


@router.get("/products")
def get_products():
    try:
        products = list(database["products"].find({}, {"_id": 0}))
        return {"count": len(products), "products": products}
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database query failed.")


@router.get("/inventory")
def get_inventory():
    try:
        inventory = list(database["inventory"].find({}, {"_id": 0}))
        return {"count": len(inventory), "inventory": inventory}
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database query failed.")


@router.get("/sales")
def get_sales():
    try:
        sales = list(database["sales"].find({}, {"_id": 0}).limit(100))
        return {"count": len(sales), "sales": sales}
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database query failed.")


@router.get("/suppliers")
def get_suppliers():
    try:
        suppliers = list(database["suppliers"].find({}, {"_id": 0}).limit(100))
        return {"count": len(suppliers), "suppliers": suppliers}
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database query failed.")


@router.post("/query")
def natural_language_query(request: QueryRequest):
    try:
        normalized_question = normalize_question(request.question)
        aggregation = generate_aggregation_query(normalized_question)

        if aggregation is not None:
            collection_name = aggregation.get("collection")
            pipeline = aggregation.get("pipeline")

            if collection_name not in ALLOWED_COLLECTIONS:
                raise HTTPException(
                    status_code=400,
                    detail="Aggregation selected an unsupported collection.",
                )

            try:
                validate_aggregation_pipeline(pipeline, collection_name)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail="Generated aggregation contains an unsupported stage or field.",
                )

            results = list(
                database[collection_name].aggregate(pipeline)
            )

            return {
                "question": request.question,
                "collection": collection_name,
                "query_type": "aggregate",
                "generation_method": "aggregation_rule_based",
                "generated_query": pipeline,
                "description": aggregation.get("description", ""),
                "similar_examples": [],
                "count": len(results),
                "results": results,
            }

        scope_error = question_scope_error(normalized_question)
        if scope_error:
            raise HTTPException(status_code=400, detail=scope_error)

        searcher = get_semantic_search()
        matches = searcher.search(normalized_question, top_k=3)

        similar_examples = [
            {
                "question": item["example"]["question"],
                "similarity": item["similarity"],
            }
            for item in matches
        ]

        generated = None
        method = None

        # Try the existing rule-based generator first.
        try:
            generated = generate_query(normalized_question)
            method = "rule_based"
        except ValueError:
            generated = None

        # Use the LLM if the rule-based generator cannot understand the question.
        if generated is None:
            try:
                generated = generate_llm_query(normalized_question)
                method = "groq_llm"
            except Exception:
                # Existing examples may help with familiar product/inventory questions.
                if matches and matches[0]["similarity"] >= MIN_SIMILARITY:
                    example = matches[0]["example"]
                    if example.get("collection") in ALLOWED_COLLECTIONS:
                        generated = {
                            "collection": example["collection"],
                            "filter": example["filter"],
                            "description": example.get("description", ""),
                        }
                        method = "semantic_example_fallback"
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Could not generate a supported query. Please rephrase your question.",
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Question could not be understood confidently. "
                            "Try rephrasing it in simple English."
                        ),
                    )

        collection_name = generated.get("collection")
        query_filter = generated.get("filter")

        if collection_name not in ALLOWED_COLLECTIONS:
            raise HTTPException(
                status_code=400,
                detail="The generated query selected an unsupported collection.",
            )

        if not isinstance(query_filter, dict):
            raise HTTPException(status_code=400, detail="Invalid query filter.")

        if collection_name == "products":
            query_filter = normalize_category_filter(query_filter)

        try:
            validate_filter(query_filter, COLLECTION_FIELDS[collection_name])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Generated query contains an unsupported field or operator.",
            )

        results = list(
            database[collection_name]
            .find(query_filter, {"_id": 0})
            .limit(100)
        )

        return {
            "question": request.question,
            "collection": collection_name,
            "generation_method": method,
            "generated_query": query_filter,
            "description": generated.get("description", ""),
            "similar_examples": similar_examples,
            "count": len(results),
            "results": results,
        }

    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database query failed.")
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Query processing failed. Check the backend logs.",
        )

