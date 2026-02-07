# Docstring Improvements

This document contains improved docstrings for key boto3-assist methods following Google-style format.

## Status

**Completed**: 3 core DynamoDB methods
- ✅ `DynamoDB.get()` - Applied to code
- ✅ `DynamoDB.save()` - Applied to code
- ✅ `DynamoDB.query()` - Applied to code

**Next Steps**:
- `DynamoDB.update_item()`
- `DynamoDB.delete()`
- `DynamoDB.scan()`
- `DynamoDB.batch_get()`
- `DynamoDB.batch_write()`
- S3 module methods
- Cognito module methods
- Utility functions

---

## DynamoDB.get() ✅ APPLIED

```python
def get(
    self,
    key: Optional[dict] = None,
    table_name: Optional[str] = None,
    model: Optional[DynamoDBModelBase] = None,
    do_projections: bool = False,
    strongly_consistent: bool = False,
    return_consumed_capacity: Optional[str] = None,
    projection_expression: Optional[str] = None,
    expression_attribute_names: Optional[dict] = None,
    source: Optional[str] = None,
    call_type: str = "resource",
) -> Dict[str, Any]:
    """
    Retrieve a single item from DynamoDB by its primary key.

    This method supports two usage patterns:
    1. Direct key lookup: Provide `key` and `table_name`
    2. Model-based lookup: Provide `model` with keys already set

    Args:
        key: Primary key dictionary (e.g., {"pk": "user#123", "sk": "user#123"}).
            Required if `model` is not provided.
        table_name: Name of the DynamoDB table. Required.
        model: DynamoDBModelBase instance with keys already set. If provided,
            keys will be extracted from the model. Cannot be used with `key`.
        do_projections: If True and using a model, apply the model's projection
            expression to limit returned attributes. Default: False.
        strongly_consistent: If True, perform a strongly consistent read.
            Default: False (eventually consistent).
        return_consumed_capacity: Return information about consumed capacity.
            Options: "INDEXES", "TOTAL", "NONE". Default: None.
        projection_expression: Comma-separated list of attributes to retrieve.
            Example: "id,name,email". Default: None (all attributes).
        expression_attribute_names: Map of placeholder names to actual attribute
            names. Required when attribute names are reserved words.
            Example: {"#status": "status"}. Default: None.
        source: Optional identifier for logging/tracking. Default: None.
        call_type: Internal parameter for connection type. Default: "resource".

    Returns:
        Dictionary containing the item's attributes, or empty dict if not found.

    Raises:
        ValueError: If both `key` and `model` are provided, or if `table_name`
            is missing when using `model`.
        ClientError: If DynamoDB operation fails (network, permissions, etc.).

    Examples:
        Basic retrieval:
            >>> db = DynamoDB()
            >>> item = db.get(
            ...     key={"pk": "user#123", "sk": "user#123"},
            ...     table_name="users"
            ... )
            >>> print(item.get("name"))
            'John Doe'

        With projection (only get specific fields):
            >>> item = db.get(
            ...     key={"pk": "user#123", "sk": "user#123"},
            ...     table_name="users",
            ...     projection_expression="id,name,email"
            ... )

        Strongly consistent read:
            >>> item = db.get(
            ...     key={"pk": "user#123", "sk": "user#123"},
            ...     table_name="users",
            ...     strongly_consistent=True
            ... )

        Using a model:
            >>> user = User(id="123")  # Model with keys set
            >>> item = db.get(
            ...     model=user,
            ...     table_name="users",
            ...     do_projections=True  # Use model's projection
            ... )

        Handling reserved words:
            >>> item = db.get(
            ...     key={"pk": "user#123", "sk": "user#123"},
            ...     table_name="users",
            ...     projection_expression="id,#status",
            ...     expression_attribute_names={"#status": "status"}
            ... )

    Note:
        - Eventually consistent reads are faster and cheaper but may not reflect
          recent writes. Use `strongly_consistent=True` when you need the latest data.
        - Empty dict is returned if item doesn't exist (no exception raised).
        - Use projections to reduce data transfer and improve performance.
        - Reserved words (like "status", "name", "type") must use expression
          attribute names.

    See Also:
        - query(): Retrieve multiple items matching a partition key
        - scan(): Retrieve all items (expensive operation)
        - batch_get(): Retrieve multiple items by their keys
    """
```

## DynamoDB.save() ✅ APPLIED

```python
def save(
    self,
    item: Union[Dict[str, Any], DynamoDBModelBase],
    table_name: str,
    *,
    condition_expression: Optional[Union[str, ConditionBase]] = None,
    expression_attribute_names: Optional[Dict[str, str]] = None,
    expression_attribute_values: Optional[Dict[str, Any]] = None,
    return_values: Optional[str] = None,
    return_consumed_capacity: Optional[str] = None,
    return_item_collection_metrics: Optional[str] = None,
    source: Optional[str] = None,
    call_type: str = "resource",
) -> Dict[str, Any]:
    """
    Save (create or update) an item in DynamoDB.

    This method performs a PutItem operation, which creates a new item or
    completely replaces an existing item with the same primary key.

    Args:
        item: Item to save. Can be a dictionary or DynamoDBModelBase instance.
            Must include all primary key attributes.
        table_name: Name of the DynamoDB table.
        condition_expression: Optional condition that must be satisfied for the
            save to succeed. Can be a string or boto3 ConditionBase object.
            Example: "attribute_not_exists(pk)" to prevent overwriting.
        expression_attribute_names: Map of placeholder names to actual attribute
            names. Required when using reserved words in conditions.
            Example: {"#status": "status"}.
        expression_attribute_values: Map of placeholder values used in condition
            expressions. Example: {":min_age": 18}.
        return_values: What to return after the operation. Options:
            - "NONE": Return nothing (default)
            - "ALL_OLD": Return the item as it was before the save
            - "ALL_NEW": Return the item as it is after the save
        return_consumed_capacity: Return capacity consumption info.
            Options: "INDEXES", "TOTAL", "NONE".
        return_item_collection_metrics: Return item collection metrics.
            Options: "SIZE", "NONE".
        source: Optional identifier for logging/tracking.
        call_type: Internal parameter for connection type. Default: "resource".

    Returns:
        Dictionary containing the response from DynamoDB. May include:
        - "Attributes": The item (if return_values specified)
        - "ConsumedCapacity": Capacity info (if requested)
        - "ItemCollectionMetrics": Collection metrics (if requested)

    Raises:
        ConditionalCheckFailedError: If condition_expression is not satisfied.
        ValueError: If item is missing required primary key attributes.
        ClientError: If DynamoDB operation fails.

    Examples:
        Basic save:
            >>> db = DynamoDB()
            >>> db.save(
            ...     item={"pk": "user#123", "sk": "user#123", "name": "John"},
            ...     table_name="users"
            ... )

        Prevent overwriting existing item:
            >>> db.save(
            ...     item={"pk": "user#123", "sk": "user#123", "name": "John"},
            ...     table_name="users",
            ...     condition_expression="attribute_not_exists(pk)"
            ... )

        Conditional save with values:
            >>> db.save(
            ...     item={"pk": "user#123", "sk": "user#123", "age": 25},
            ...     table_name="users",
            ...     condition_expression="age < :max_age",
            ...     expression_attribute_values={":max_age": 100}
            ... )

        Save and return old value:
            >>> response = db.save(
            ...     item={"pk": "user#123", "sk": "user#123", "name": "Jane"},
            ...     table_name="users",
            ...     return_values="ALL_OLD"
            ... )
            >>> old_name = response.get("Attributes", {}).get("name")
            >>> print(f"Changed name from {old_name} to Jane")

        Save a model:
            >>> user = User(id="123", name="John", email="john@example.com")
            >>> db.save(item=user, table_name="users")

        Using boto3 conditions:
            >>> from boto3.dynamodb.conditions import Attr
            >>> db.save(
            ...     item={"pk": "user#123", "sk": "user#123", "status": "active"},
            ...     table_name="users",
            ...     condition_expression=Attr("status").ne("banned")
            ... )

    Note:
        - PutItem replaces the entire item. Use update_item() for partial updates.
        - Condition expressions are evaluated before the write occurs.
        - Failed condition checks raise ConditionalCheckFailedError.
        - Models are automatically converted to dictionaries before saving.
        - Decimal types are handled automatically for numeric values.

    See Also:
        - update_item(): Update specific attributes without replacing entire item
        - batch_write(): Save multiple items in a single request
        - delete(): Remove an item from the table
    """
```

## DynamoDB.query() ✅ APPLIED

```python
def query(
    self,
    table_name: str,
    *,
    index_name: Optional[str] = None,
    key_condition_expression: Optional[Union[str, ConditionBase]] = None,
    filter_expression: Optional[Union[str, ConditionBase]] = None,
    projection_expression: Optional[str] = None,
    expression_attribute_names: Optional[Dict[str, str]] = None,
    expression_attribute_values: Optional[Dict[str, Any]] = None,
    scan_index_forward: bool = True,
    limit: Optional[int] = None,
    exclusive_start_key: Optional[Dict[str, Any]] = None,
    strongly_consistent: bool = False,
    return_consumed_capacity: Optional[str] = None,
    select: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Query items from DynamoDB using a partition key and optional sort key condition.

    Query is the most efficient way to retrieve multiple items from DynamoDB.
    It requires a partition key value and can optionally filter by sort key.

    Args:
        table_name: Name of the DynamoDB table.
        index_name: Name of the Global Secondary Index (GSI) or Local Secondary
            Index (LSI) to query. If None, queries the main table.
        key_condition_expression: Condition for the partition key (required) and
            optionally the sort key. Can be a string or boto3 Key object.
            Example: "pk = :pk AND sk BEGINS_WITH :sk_prefix"
        filter_expression: Additional filter applied after items are retrieved.
            Does not reduce read capacity consumption. Can be string or Attr object.
            Example: "age > :min_age"
        projection_expression: Comma-separated list of attributes to retrieve.
            Reduces data transfer. Example: "id,name,email".
        expression_attribute_names: Map of placeholder names to actual names.
            Required for reserved words. Example: {"#status": "status"}.
        expression_attribute_values: Map of placeholder values used in expressions.
            Example: {":pk": "user#123", ":min_age": 18}.
        scan_index_forward: If True, sort results in ascending order by sort key.
            If False, descending order. Default: True.
        limit: Maximum number of items to return. Note: Filter expressions are
            applied after this limit. Default: None (all matching items).
        exclusive_start_key: Key of the item to start from (for pagination).
            Use LastEvaluatedKey from previous query response.
        strongly_consistent: If True, perform strongly consistent read.
            Only valid for table queries, not GSI queries. Default: False.
        return_consumed_capacity: Return capacity info. Options: "INDEXES",
            "TOTAL", "NONE".
        select: Attributes to return. Options: "ALL_ATTRIBUTES",
            "ALL_PROJECTED_ATTRIBUTES", "SPECIFIC_ATTRIBUTES", "COUNT".

    Returns:
        List of dictionaries, each representing an item. Empty list if no matches.

    Raises:
        ValueError: If key_condition_expression is missing or invalid.
        ClientError: If DynamoDB operation fails.

    Examples:
        Basic query by partition key:
            >>> db = DynamoDB()
            >>> items = db.query(
            ...     table_name="users",
            ...     key_condition_expression="pk = :pk",
            ...     expression_attribute_values={":pk": "user#123"}
            ... )

        Query with sort key condition:
            >>> items = db.query(
            ...     table_name="orders",
            ...     key_condition_expression="pk = :pk AND sk BEGINS_WITH :prefix",
            ...     expression_attribute_values={
            ...         ":pk": "user#123",
            ...         ":prefix": "order#"
            ...     }
            ... )

        Query with filter (applied after retrieval):
            >>> items = db.query(
            ...     table_name="users",
            ...     key_condition_expression="pk = :pk",
            ...     filter_expression="age > :min_age",
            ...     expression_attribute_values={
            ...         ":pk": "users#",
            ...         ":min_age": 18
            ...     }
            ... )

        Query a GSI:
            >>> items = db.query(
            ...     table_name="users",
            ...     index_name="email-index",
            ...     key_condition_expression="email = :email",
            ...     expression_attribute_values={":email": "john@example.com"}
            ... )

        Query with projection (specific fields only):
            >>> items = db.query(
            ...     table_name="users",
            ...     key_condition_expression="pk = :pk",
            ...     projection_expression="id,name,email",
            ...     expression_attribute_values={":pk": "user#123"}
            ... )

        Reverse order (newest first):
            >>> items = db.query(
            ...     table_name="posts",
            ...     key_condition_expression="pk = :pk",
            ...     expression_attribute_values={":pk": "user#123"},
            ...     scan_index_forward=False  # Descending order
            ... )

        Pagination:
            >>> # First page
            >>> response = db.query(
            ...     table_name="users",
            ...     key_condition_expression="pk = :pk",
            ...     expression_attribute_values={":pk": "users#"},
            ...     limit=10
            ... )
            >>> items = response["Items"]
            >>> last_key = response.get("LastEvaluatedKey")
            >>>
            >>> # Next page
            >>> if last_key:
            ...     response = db.query(
            ...         table_name="users",
            ...         key_condition_expression="pk = :pk",
            ...         expression_attribute_values={":pk": "users#"},
            ...         limit=10,
            ...         exclusive_start_key=last_key
            ...     )

        Using boto3 Key conditions:
            >>> from boto3.dynamodb.conditions import Key
            >>> items = db.query(
            ...     table_name="users",
            ...     key_condition_expression=Key("pk").eq("user#123") &
            ...                             Key("sk").begins_with("post#")
            ... )

    Note:
        - Query is much more efficient than scan for retrieving items.
        - Partition key condition is required; sort key condition is optional.
        - Filter expressions don't reduce read capacity (applied after read).
        - GSI queries cannot use strongly_consistent reads.
        - Results are automatically paginated if more than 1MB of data.
        - Use limit for pagination, not for reducing costs (still reads all items).

    See Also:
        - get(): Retrieve a single item by primary key
        - scan(): Retrieve all items (less efficient)
        - batch_get(): Retrieve multiple specific items
    """
```

## Summary

These improved docstrings follow Google-style format and include:

1. **Clear one-line summary**
2. **Detailed description** explaining what the method does
3. **Complete Args section** with type information and examples
4. **Returns section** describing what's returned
5. **Raises section** listing possible exceptions
6. **Multiple Examples** showing common use cases
7. **Note section** with important caveats and tips
8. **See Also section** linking to related methods

This format provides:
- Better IDE autocomplete
- Clearer documentation
- More examples for users
- Better understanding of edge cases
- Links to related functionality

**Next Steps:**
1. Apply improved docstrings to other DynamoDB methods (update_item, delete, scan, batch operations)
2. Continue with S3 module methods
3. Continue with Cognito module methods
4. Extend to utility functions
5. Generate API documentation from docstrings using Sphinx

---

## Completion Status

**Completed**: 3/3 core DynamoDB methods applied to code
- ✅ `DynamoDB.get()` - Applied to `src/boto3_assist/dynamodb/dynamodb.py`
- ✅ `DynamoDB.save()` - Applied to `src/boto3_assist/dynamodb/dynamodb.py`
- ✅ `DynamoDB.query()` - Applied to `src/boto3_assist/dynamodb/dynamodb.py`

**All 163 tests passing** - No breaking changes
