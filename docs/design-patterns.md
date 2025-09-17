# AWS SaaS Design Patterns with boto3-assist

This document outlines comprehensive design patterns for building scalable SaaS applications, leveraging boto3-assist for AWS DynamoDB and other services. These patterns provide a standardized, scalable architecture for multi-tenant SaaS applications.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Design Patterns](#core-design-patterns)
3. [Model Layer Patterns](#model-layer-patterns)
4. [Service Layer Patterns](#service-layer-patterns)
5. [Lambda Handler Patterns](#lambda-handler-patterns)
6. [Data Transformation Patterns](#data-transformation-patterns)
7. [Infrastructure Integration Patterns](#infrastructure-integration-patterns)
8. [Testing Patterns](#testing-patterns)
9. [Performance Optimization Patterns](#performance-optimization-patterns)
10. [Monitoring & Observability Patterns](#monitoring--observability-patterns)
11. [Security Enhancement Patterns](#security-enhancement-patterns)
12. [Migration & Evolution Patterns](#migration--evolution-patterns)
13. [Cost Optimization Patterns](#cost-optimization-patterns)
14. [Disaster Recovery Patterns](#disaster-recovery-patterns)
15. [API Versioning Patterns](#api-versioning-patterns)
16. [Configuration Management](#configuration-management)

## Architecture Overview

This architecture follows a layered design with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│        Frontend (SPA Framework)         │
│              (camelCase)                │
└─────────────────┬───────────────────────┘
                  │ HTTP/API Gateway
┌─────────────────▼───────────────────────┐
│         Lambda Handlers Layer           │
│    (Authentication, CORS, Routing)      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Service Layer                  │
│     (Business Logic, Validation)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Model Layer                    │
│    (DynamoDB Models, boto3-assist)      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         AWS DynamoDB                    │
│      (Single Table Design)              │
└─────────────────────────────────────────┘
```

## Core Design Patterns

### 1. Single Table Design with boto3-assist

**Pattern**: Use DynamoDB single table design with boto3-assist's `DynamoDBModelBase` for all entities.

**Implementation**:
```python
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase

class BaseDBModel(DynamoDBModelBase):
    def __init__(self) -> None:
        super().__init__()
        self.id: str = StringUtility.generate_sortable_uuid()
        self.__created_utc: dt.datetime = dt.datetime.now(dt.UTC)
        self.__updated_utc: dt.datetime = dt.datetime.now(dt.UTC)
        # ... other common fields
```

**Benefits**:
- Consistent data access patterns
- Automatic serialization/deserialization
- Built-in DynamoDB operations
- Sortable UUIDs for time-based ordering

### 2. Tenant-Based Multi-Tenancy

**Pattern**: All models inherit from `BaseTenantUserDBModel` to enforce tenant isolation.

**Implementation**:
```python
class BaseTenantUserDBModel(BaseDBModel):
    def __init__(self) -> None:
        super().__init__()
        self.tenant_id: str = ""
        self.user_id: str = ""
        # Automatic indexing for tenant-based queries
```

**Benefits**:
- Automatic tenant isolation
- Consistent access patterns
- Built-in user context tracking

### 3. Service Factory Pattern

**Pattern**: Centralized service creation with dependency injection support.

**Implementation**:
```python
class ServiceFactory:
    def __init__(self, db: Optional[DynamoDB] = None) -> None:
        self.__db: Optional[DynamoDB] = db
        # Lazy-loaded service instances
    
    @property
    def group_service(self) -> "GroupService":
        if self.__group_service is None:
            table_name = os.environ.get("APP_TABLE_NAME")
            self.__group_service = GroupService(self.db, table_name)
        return self.__group_service
```

**Benefits**:
- Centralized configuration management
- Easy testing with dependency injection
- Lazy loading for performance
- Environment-based configuration

## Model Layer Patterns

### 1. Models as Data Transport Objects (DTOs)

**Pattern**: Models are used exclusively for data transport and serialization. They do NOT contain business logic or database interaction methods.

**Key Principles**:
- **Transport Only**: Models represent data structure and validation
- **No Database Operations**: Models never directly interact with DynamoDB
- **Services Handle Persistence**: All CRUD operations are performed by service classes
- **Serialization Focus**: Models handle conversion between formats (camelCase ↔ snake_case)

**Separation of Concerns**:
```python
# ✅ CORRECT: Model only defines structure
class User(BaseDBModel):
    def __init__(self):
        super().__init__()
        self.email: str = ""
        self.name: str = ""
    
    # Only transport methods allowed
    def to_ui_payload(self) -> Dict[str, Any]:
        return JsonConversions.json_snake_to_camel(self.to_dictionary())

# ❌ INCORRECT: Model should NOT have database methods
class User(BaseDBModel):
    def save(self):  # DON'T DO THIS
        # Database operations belong in services
        pass
```

### 2. Base Model with Common Properties

**Pattern**: All models inherit from `BaseDBModel` with standard audit fields.

**Key Features**:
- Automatic UUID generation with sortable timestamps
- Created/Updated/Deleted timestamp tracking
- Model versioning support
- Metadata support for extensibility
- Cross-reference support for relationships

### 2. Automatic Case Conversion

**Pattern**: Models automatically handle camelCase ↔ snake_case conversion for UI integration.

**Implementation**:
```python
@classmethod
def from_ui_payload(cls, payload: Dict[str, Any]) -> 'BaseDBModel':
    """Create model from UI camelCase payload"""
    snake_case_payload = JsonConversions.json_camel_to_snake(payload)
    instance = cls()
    instance.map(snake_case_payload)
    return instance

def to_ui_payload(self) -> Dict[str, Any]:
    """Convert model to UI camelCase format"""
    model_dict = self.to_dictionary()
    return JsonConversions.json_snake_to_camel(model_dict)
```

### 3. Model Name Convention

**Pattern**: Automatic model naming using class name conversion.

**Implementation**:
```python
@property
def model_name(self) -> str:
    """Returns snake_case model name from class name"""
    return StringUtility.camel_to_snake(self.__class__.__name__)
```

**Example**: `UserProfile` class → `user_profile` model name

### 4. DynamoDB Index Design Patterns

**Pattern**: Use boto3-assist's `DynamoDBIndex` and `DynamoDBKey.build_key()` for creating composite keys in single table design with direct index setup in model constructors.

#### Core Index Principles

1. **Composite Key Structure**: Use `DynamoDBKey.build_key()` to create hierarchical composite keys
2. **Direct Index Setup**: Define indexes directly in model constructor for simplicity and consistency
3. **Lambda-Based Key Generation**: Use lambda functions for dynamic key generation
4. **Consistent Naming**: GSI names follow `gsi1`, `gsi2`, etc. with corresponding attribute names

#### Index Implementation Pattern

**Model Structure (Direct Index Setup)**:
```python
from typing import Optional, Dict, Any
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
# Note: BaseTenantUserDBModel would be your custom base class
# from your_project.models.base_tenant_user_model import BaseTenantUserDBModel

class Group(BaseTenantUserDBModel):  # Your custom tenant-aware base class
    """Group model with direct index setup in constructor"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name: str = ""
        self.description: str = ""
        self.group_type: str = ""
        self.icon: Optional[str] = None
        self.color: Optional[str] = None
        self.privacy_settings: Optional[Dict[str, Any]] = {"visibility": "private"}
        
        # Setup indexes directly in constructor (boto3-assist pattern)
        self._setup_indexes()

    def _setup_indexes(self):
        """Setup all indexes with error handling"""
        try:
            self._setup_primary_key()
            self._setup_user_type_index()
            self._setup_tenant_type_index()
            self._setup_tenant_time_index()
        except Exception as e:
            raise ValueError(f"Failed to setup indexes: {e}")

    def _setup_primary_key(self):
        """
        Primary Key Pattern:
        PK: group#id
        SK: group#id
        Enables: Direct item lookup by ID
        """
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            (self.model_name, self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            (self.model_name, self.id)
        )
        self.indexes.add_primary(primary)

    def _setup_user_type_index(self):        
        """ 
        GSI1: User-Type-Name Index
        PK: group##user#user_id#type#group_type
        SK: name#group_name
        Enables: "Get all groups for a user by type, sorted by name"
        """
        gsi1: DynamoDBIndex = DynamoDBIndex(index_name="gsi1")
        gsi1.partition_key.attribute_name = "gsi1_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(
            (self.model_name, ""), 
            ("user", self.user_id), 
            ("type", self.group_type)
        )
        gsi1.sort_key.attribute_name = "gsi1_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(
           ("name", self.name or "")
        )
        self.indexes.add_secondary(gsi1)
    
    def _setup_tenant_type_index(self):
        """
        GSI2: Tenant-Type-Name Index
        PK: group##tenant#tenant_id#type#group_type
        SK: name#group_name
        Enables: "Get all groups for a tenant by type, sorted by name"
        """
        gsi2: DynamoDBIndex = DynamoDBIndex(index_name="gsi2")
        gsi2.partition_key.attribute_name = "gsi2_pk"
        gsi2.partition_key.value = lambda: DynamoDBKey.build_key(
            (self.model_name, ""), 
            ("tenant", self.tenant_id), 
            ("type", self.group_type)
        )
        gsi2.sort_key.attribute_name = "gsi2_sk"
        gsi2.sort_key.value = lambda: DynamoDBKey.build_key(
           ("name", self.name or "")
        )
        self.indexes.add_secondary(gsi2)

    def _setup_tenant_time_index(self):
        """
        GSI3: Tenant-Time Index
        PK: group##tenant#tenant_id
        SK: created#1705312200
        Enables: "Get all groups for a tenant by creation time"
        Uses Unix timestamp for efficient numeric sorting and range queries
        """
        gsi3: DynamoDBIndex = DynamoDBIndex(index_name="gsi3")
        gsi3.partition_key.attribute_name = "gsi3_pk"
        gsi3.partition_key.value = lambda: DynamoDBKey.build_key(
            (self.model_name, ""), 
            ("tenant", self.tenant_id)
        )
        gsi3.sort_key.attribute_name = "gsi3_sk"
        gsi3.sort_key.value = lambda: DynamoDBKey.build_key(
            ("created", str(int(self.created_utc.timestamp())) if self.created_utc else "0")
        )
        self.indexes.add_secondary(gsi3)
```

**Best Practices for Index Setup**:
- Always setup indexes in the model constructor using `_setup_indexes()`
- Use descriptive method names for each index setup (`_setup_primary_key`, `_setup_user_type_index`)
- Include error handling in the setup process
- Use lambda functions for dynamic key generation to ensure proper value binding
- Follow consistent GSI naming: `gsi1`, `gsi2`, etc.
- **Use Unix timestamps for time-based sort keys** for better performance and range queries

#### Common Index Patterns

**A. User-Based Queries (GSI1)**
```python
# Query Pattern: Get all "favorite" groups for a user, sorted by name
# PK: group##user#user123#type#favorite
# SK: name#My Favorites

def _setup_user_type_index(self):
    gsi: DynamoDBIndex = DynamoDBIndex()
    gsi.name = "gsi1"
    gsi.partition_key.attribute_name = "gsi1_pk"
    gsi.partition_key.value = lambda: DynamoDBKey.build_key(
        (self.model.model_name, ""), 
        ("user", self.model.user_id), 
        ("type", self.model.group_type)
    )
    gsi.sort_key.attribute_name = "gsi1_sk"
    gsi.sort_key.value = lambda: DynamoDBKey.build_key(
        ("name", self.model.name or "")
    )
    self.model.indexes.add_secondary(gsi)
```

**B. Tenant-Based Queries (GSI2)**
```python
# Query Pattern: Get all "watchlist" groups for a tenant, sorted by name
# PK: group##tenant#tenant456#type#watchlist
# SK: name#Property Watchlist

def _setup_tenant_type_index(self):
    gsi: DynamoDBIndex = DynamoDBIndex()
    gsi.name = "gsi2"
    gsi.partition_key.attribute_name = "gsi2_pk"
    gsi.partition_key.value = lambda: DynamoDBKey.build_key(
        (self.model.model_name, ""), 
        ("tenant", self.model.tenant_id), 
        ("type", self.model.group_type)
    )
    gsi.sort_key.attribute_name = "gsi2_sk"
    gsi.sort_key.value = lambda: DynamoDBKey.build_key(
        ("name", self.model.name)
    )
    self.model.indexes.add_secondary(gsi)
```

**C. Time-Based Queries (GSI3)**
```python
# Query Pattern: Get all groups for a tenant by creation time (newest first)
# PK: group##tenant#tenant123
# SK: created#1705312200

def _setup_tenant_time_index(self):
    gsi3: DynamoDBIndex = DynamoDBIndex(index_name="gsi3")
    gsi3.partition_key.attribute_name = "gsi3_pk"
    gsi3.partition_key.value = lambda: DynamoDBKey.build_key(
        (self.model.model_name, ""), 
        ("tenant", self.model.tenant_id)
    )
    gsi3.sort_key.attribute_name = "gsi3_sk"
    gsi3.sort_key.value = lambda: DynamoDBKey.build_key(
        ("created", str(int(self.model.created_utc.timestamp())) if self.model.created_utc else "0")
    )
    self.model.indexes.add_secondary(gsi3)

# Query examples with timestamps:
# - Last 24 hours: SK > str(int((datetime.now() - timedelta(days=1)).timestamp()))
# - Specific date range: SK BETWEEN "1705312200" AND "1705398600"
# - This week: SK > str(int((datetime.now() - timedelta(weeks=1)).timestamp()))
```

#### Service Query Patterns

**Standard Service Implementation**:
```python
from typing import List, Dict, Any, Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from movatra_saas_models.groups.group import Group

class GroupService(BaseService):
    """
    Standard service implementation following movatra patterns:
    - Model-based DynamoDB operations
    - Explicit parameter control for production robustness
    - Consistent ServiceResult error handling
    """
    
    def __init__(self, db: Optional[DynamoDB] = None):
        self.db: DynamoDB = db or DynamoDB()
        self.table_name: str = os.environ.get("APP_TABLE_NAME", "default-table")
    
    def get_by_id(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[Group]:
        """Get group by ID using enhanced model-based get method"""
        try:
            # Create model instance with ID
            group = Group()
            group.id = resource_id

            # Use model-based get method with explicit parameters
            result = self.db.get(
                model=group,
                table_name=self.table_name,
                do_projections=False,
                strongly_consistent=False
            )

            item = result.get("Item", {})
            if not item:
                return ServiceResult.error_result("Group not found", "NOT_FOUND")

            # Map the result to model instance
            group = Group().map(item)

            # Validate access
            if group.user_id != user_id:
                return ServiceResult.error_result("Access denied", "ACCESS_DENIED")

            return ServiceResult.success_result(group)

        except Exception as e:
            return ServiceResult.error_result(f"Failed to get group: {str(e)}", "ERROR")
    
    def list_by_user_and_type(self, user_id: str, group_type: str, tenant_id: str) -> ServiceResult[List[Group]]:
        """Query using GSI1 (User-Type-Name Index)"""
        try:
            # Create model instance with query parameters
            model = Group()
            model.user_id = user_id
            model.tenant_id = tenant_id
            model.group_type = group_type
            
            # Use model-based query method
            result = self.db.query_by_criteria(
                model=model,
                index_name="gsi1",
                table_name=self.table_name,
                do_projections=False,
                strongly_consistent=False,
                ascending=True
            )

            # Map results to model instances
            groups = [Group().map(item) for item in result.get("Items", [])]
            return ServiceResult.success_result(groups)

        except Exception as e:
            return ServiceResult.error_result(f"Failed to get groups by user and type: {str(e)}", "ERROR")
    
    def list_by_tenant_time_range(self, tenant_id: str, start_timestamp: int = None, end_timestamp: int = None) -> ServiceResult[List[Group]]:
        """Query using GSI3 (Tenant-Time Index) with timestamp range"""
        try:
            # Create model instance with query parameters
            model = Group()
            model.tenant_id = tenant_id
            
            # Build key condition with timestamp range if provided
            key_condition = model.get_key("gsi3").key()
            
            # Add range condition if timestamps provided
            filter_expression = None
            if start_timestamp or end_timestamp:
                if start_timestamp and end_timestamp:
                    filter_expression = f"gsi3_sk BETWEEN :start_ts AND :end_ts"
                    expression_values = {
                        ":start_ts": f"created#{start_timestamp}",
                        ":end_ts": f"created#{end_timestamp}"
                    }
                elif start_timestamp:
                    filter_expression = f"gsi3_sk >= :start_ts"
                    expression_values = {":start_ts": f"created#{start_timestamp}"}
                elif end_timestamp:
                    filter_expression = f"gsi3_sk <= :end_ts"
                    expression_values = {":end_ts": f"created#{end_timestamp}"}
            
            # Use model-based query method
            result = self.db.query_by_criteria(
                model=model,
                index_name="gsi3",
                table_name=self.table_name,
                do_projections=False,
                strongly_consistent=False,
                ascending=False,  # Newest first
                filter_expression=filter_expression if start_timestamp or end_timestamp else None,
                expression_attribute_values=expression_values if start_timestamp or end_timestamp else None
            )

            groups = [Group().map(item) for item in result.get("Items", [])]
            return ServiceResult.success_result(groups)

        except Exception as e:
            return ServiceResult.error_result(f"Failed to get groups by time range: {str(e)}", "ERROR")
    
    def create(self, tenant_id: str, user_id: str, **kwargs) -> ServiceResult[Group]:
        """Create new group"""
        try:
            # Create new group instance
            group = Group()
            group.user_id = user_id
            group.tenant_id = tenant_id
            group.map(kwargs)

            # Save using model serialization
            self.db.save(
                item=group.to_resource_dictionary(), 
                table_name=self.table_name
            )

            return ServiceResult.success_result(group)

        except Exception as e:
            return ServiceResult.error_result(f"Failed to create group: {str(e)}", "ERROR")
    
    def update(self, resource_id: str, tenant_id: str, user_id: str, updates: Dict[str, Any]) -> ServiceResult[Group]:
        """Update group using get-modify-save pattern"""
        try:
            # Get existing group first
            get_result = self.get_by_id(resource_id, tenant_id, user_id)
            if not get_result.success:
                return get_result

            group = get_result.data

            # Apply updates and save
            group.map(updates)
            self.db.save(
                item=group.to_resource_dictionary(), 
                table_name=self.table_name
            )

            return ServiceResult.success_result(group)

        except Exception as e:
            return ServiceResult.error_result(f"Failed to update group: {str(e)}", "ERROR")
    
    def delete(self, resource_id: str, tenant_id: str, user_id: str) -> ServiceResult[bool]:
        """Delete group"""
        try:
            # Get existing group first to validate access
            get_result = self.get_by_id(resource_id, tenant_id, user_id)
            if not get_result.success:
                return ServiceResult.error_result("Group not found or access denied", "NOT_FOUND")

            group = get_result.data

            # Delete using model-based method
            self.db.delete(model=group, table_name=self.table_name)

            return ServiceResult.success_result(True)

        except Exception as e:
            return ServiceResult.error_result(f"Failed to delete group: {str(e)}", "ERROR")
```

**Best Practices for Service Implementation**:
- Always use `ServiceResult` for consistent error handling and response format
- Create model instances and set required properties before database operations
- Use explicit parameters (`do_projections`, `strongly_consistent`) for production control
- Map database results using `.map()` method for proper model hydration
- Use `model.get_key(index_name).key()` for robust key generation in queries
- Follow get-modify-save pattern for updates to ensure data consistency
- Validate access permissions before performing operations
- **Use Unix timestamps for time-based queries** - more efficient than ISO string comparisons
- **Leverage DynamoDB's native range operations** with timestamps for better performance


#### Index Best Practices

1. **Projection Strategy**:
   - `ALL`: Include all attributes (highest storage cost, no additional reads)
   - `KEYS_ONLY`: Only key attributes (lowest cost, requires additional reads)
   - `INCLUDE`: Specific attributes (balanced approach)

2. **Query Efficiency**:
   - Use `query()` instead of `scan()` whenever possible
   - Leverage sort key conditions for range queries
   - Use `begins_with()` for hierarchical data

3. **Cost Optimization**:
   - Minimize projected attributes for frequently queried indexes
   - Use sparse indexes to reduce storage costs
   - Consider read vs. write patterns when choosing projections

4. **Naming Conventions**:
   - Index names: `{purpose}-{sort-pattern}-index` (e.g., `tenant-time-index`)
   - Composite keys: Use `#` separator for clarity
   - Time buckets: Use ISO format for sorting (`YYYY-MM-DD`)

#### CDK Index Configuration

```python
# In your CDK stack
table = dynamodb.Table(
    self, "AppTable",
    partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="sort_key", type=dynamodb.AttributeType.STRING),
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    global_secondary_indexes=[
        dynamodb.GlobalSecondaryIndex(
            index_name="tenant-time-index",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="created_utc", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL
        ),
        dynamodb.GlobalSecondaryIndex(
            index_name="user-time-index", 
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="updated_utc", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["id", "name", "status", "tenant_id"]
        )
    ]
)
```

## Service Layer Patterns

### 1. Standard Service Structure

**Pattern**: All services follow consistent CRUD + business logic pattern.

**Base Structure**:
```python
class BaseService:
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name
    
    def create(self, **kwargs) -> ServiceResult
    def get(self, id: str, **kwargs) -> ServiceResult
    def update(self, id: str, **kwargs) -> ServiceResult
    def delete(self, id: str, **kwargs) -> ServiceResult
    def list(self, **kwargs) -> ServiceResult
    def search(self, **kwargs) -> ServiceResult
```

### 2. ServiceResult Pattern

**Pattern**: Standardized response wrapper for all service operations.

**Benefits**:
- Consistent error handling
- Success/failure status tracking
- Standardized data format
- Easy conversion to HTTP responses

### 3. Environment Variable Priority

**Pattern**: Services use environment variable fallback chain for configuration.

**Priority Order**:
Although we use the single table design pattern, we still use environment variables for configuration.  Typically it's a generic table name, but we can override it with a specific table name if needed.
1. Specific table environment variable (e.g., `GROUPS_TABLE_NAME`)
2. Generic table environment variable (e.g., `APP_TABLE_NAME`)
3. Default fallback values

## Lambda Handler Patterns

### 1. Decorator-Based Middleware

**Pattern**: Use decorators for cross-cutting concerns.

**Implementation**:
```python
@handle_cors
@require_auth
@handle_errors
def lambda_handler(event, context, injected_services=None):
    # Handler logic
```

**Middleware Functions**:
- `@handle_cors`: Automatic CORS header management
- `@require_auth`: JWT token validation and user context extraction
- `@handle_errors`: Standardized error handling and logging

### 2. Service Injection Pattern

**Pattern**: Support both production and testing service injection.

**Implementation**:
```python
def lambda_handler(event, context, injected_services=None):
    if injected_services:
        service = injected_services.group_service
    else:
        service = get_group_service()
```

### 3. Request/Response Transformation

**Pattern**: Automatic case conversion between UI and backend.

**Implementation**:
```python
# Parse request body and convert to snake_case
body = LambdaEventUtility.get_body_from_event(event)
backend_payload = LambdaEventUtility.to_snake_case_for_backend(body)

# Process with backend services
result = service.create(**backend_payload)

# Convert response to camelCase for UI
return service_result_to_response(result)
```

### 4. Standardized Response Format

**Pattern**: All handlers return consistent response structure.

**Response Structure**:
```json
{
  "data": {
    // Actual response data in camelCase
  },
  "success": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Data Transformation Patterns

### 1. Automatic Case Conversion

**Frontend → Backend**:
- UI sends camelCase
- `LambdaEventUtility.to_snake_case_for_backend()` converts to snake_case
- Backend processes with snake_case

**Backend → Frontend**:
- Backend processes with snake_case
- `service_result_to_response()` converts to camelCase
- UI receives camelCase

### 2. Serialization Utilities

**Pattern**: Use boto3-assist serialization utilities for consistent data handling.

**Key Utilities**:
- `JsonConversions.json_camel_to_snake()`
- `JsonConversions.json_snake_to_camel()`
- `StringUtility.camel_to_snake()`
- `StringUtility.generate_sortable_uuid()`

## Infrastructure Integration Patterns

### 1. SSM Parameter Integration

**Pattern**: Use AWS Systems Manager Parameter Store for cross-stack configuration.

**Configuration Structure**:
```json
{
  "ssm": {
    "enabled": true,
    "organization": "{{ORGANIZATION_NAME}}",
    "environment": "{{ENVIRONMENT}}",
    "auto_import": true
  }
}
```

**Parameter Naming Convention**:
- `/{{ORGANIZATION}}/{{ENVIRONMENT}}/service/resource/attribute`
- Example: `/mycompany/dev/dynamodb/app-table/name`

### 2. Environment Variable Standardization

**Pattern**: Use uppercase environment variables with SSM fallback.

**Naming Convention**:
- `APP_TABLE_NAME` (primary DynamoDB table)
- `USER_POOL_ARN` (Cognito user pool)
- `API_GATEWAY_URL` (API Gateway endpoint)
- `S3_BUCKET_NAME` (primary S3 bucket)

### 3. CDK Integration Patterns

**Pattern**: Automatic API Gateway integration when Lambda functions define API configuration.

**Features**:
- Automatic route creation and binding
- Support for existing API Gateway references
- Cognito authorizer integration
- CORS configuration
- Environment variable injection

## Testing Patterns

### 1. Service Factory Testing

**Pattern**: Use dependency injection for isolated unit testing.

**Implementation**:
```python
def test_create_group():
    # Mock DynamoDB
    mock_db = Mock()
    factory = ServiceFactory(db=mock_db)
    
    # Test with injected services
    result = lambda_handler(event, context, injected_services=factory)
```

### 2. Environment Loading

**Pattern**: Automatic test environment setup with file discovery.

**Implementation**:
```python
factory = ServiceFactory()
event = factory.load_test_env(
    starting_path=os.path.dirname(__file__),
    env_file_name=".env.development",
    event_file_name="test.json"
)
```

### 3. Moto Integration

**Pattern**: Use moto for AWS service mocking in integration tests.

**Benefits**:
- Real AWS API behavior simulation
- DynamoDB table creation and operations
- Cognito user pool simulation
- S3 bucket operations

## Performance Optimization Patterns

### 1. Connection Management

**Pattern**: Optimize DynamoDB connections for Lambda environments with connection reuse and warming strategies.

**Implementation**:
```python
import os
from typing import Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB

class OptimizedDynamoDBConnection:
    """Singleton pattern for DynamoDB connection management"""
    _instance: Optional['OptimizedDynamoDBConnection'] = None
    _db: Optional[DynamoDB] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def db(self) -> DynamoDB:
        if self._db is None:
            # Configure connection with optimized settings
            self._db = DynamoDB(
                region_name=os.environ.get('AWS_REGION', 'us-east-1'),
                # Connection pooling configuration
                config={
                    'max_pool_connections': 50,
                    'retries': {'max_attempts': 3, 'mode': 'adaptive'}
                }
            )
        return self._db

# Usage in services
class OptimizedService:
    def __init__(self):
        self.db = OptimizedDynamoDBConnection().db
```

**Benefits**:
- Reduces Lambda cold start impact
- Reuses connections across invocations
- Implements adaptive retry strategies
- Optimizes connection pool size

### 2. Batch Operations Pattern

**Pattern**: Use DynamoDB batch operations for bulk data processing to reduce API calls and improve throughput.

**Implementation**:
```python
from typing import List, Dict, Any
from boto3_assist.dynamodb.dynamodb import DynamoDB

class BatchOperationService:
    """Service implementing efficient batch operations"""
    
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name
        self.batch_size = 25  # DynamoDB batch limit
    
    def batch_save_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Save multiple items using batch_write_item"""
        results = []
        failed_items = []
        
        # Process in batches of 25 (DynamoDB limit)
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            try:
                # Prepare batch write request
                request_items = {
                    self.table_name: [
                        {'PutRequest': {'Item': item}} for item in batch
                    ]
                }
                
                response = self.db.client.batch_write_item(RequestItems=request_items)
                
                # Handle unprocessed items
                unprocessed = response.get('UnprocessedItems', {})
                if unprocessed:
                    failed_items.extend(unprocessed.get(self.table_name, []))
                
                results.extend(batch)
                
            except Exception as e:
                failed_items.extend(batch)
                print(f"Batch write failed: {e}")
        
        return results, failed_items
    
    def batch_get_items(self, keys: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Retrieve multiple items using batch_get_item"""
        results = []
        
        for i in range(0, len(keys), self.batch_size):
            batch_keys = keys[i:i + self.batch_size]
            
            try:
                request_items = {
                    self.table_name: {
                        'Keys': batch_keys
                    }
                }
                
                response = self.db.client.batch_get_item(RequestItems=request_items)
                items = response.get('Responses', {}).get(self.table_name, [])
                results.extend(items)
                
            except Exception as e:
                print(f"Batch get failed: {e}")
        
        return results
```

### 3. Query Optimization Patterns

**Pattern**: Implement efficient query strategies with pagination, filtering, and projection optimization.

**Implementation**:
```python
from typing import Optional, Dict, Any, List, Iterator
from boto3_assist.dynamodb.dynamodb import DynamoDB

class OptimizedQueryService:
    """Service with optimized query patterns"""
    
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name
    
    def paginated_query(
        self, 
        model: Any, 
        index_name: str,
        page_size: int = 50,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Implement efficient pagination with configurable page size"""
        
        query_params = {
            'model': model,
            'index_name': index_name,
            'table_name': self.table_name,
            'limit': page_size,
            'do_projections': True,  # Use projections to reduce data transfer
            'strongly_consistent': False,  # Use eventually consistent reads for better performance
        }
        
        if last_evaluated_key:
            query_params['exclusive_start_key'] = last_evaluated_key
        
        result = self.db.query_by_criteria(**query_params)
        
        return {
            'items': result.get('Items', []),
            'last_evaluated_key': result.get('LastEvaluatedKey'),
            'count': result.get('Count', 0),
            'scanned_count': result.get('ScannedCount', 0)
        }
    
    def stream_query_results(
        self, 
        model: Any, 
        index_name: str,
        page_size: int = 100
    ) -> Iterator[Dict[str, Any]]:
        """Stream large result sets to avoid memory issues"""
        
        last_evaluated_key = None
        
        while True:
            result = self.paginated_query(
                model=model,
                index_name=index_name,
                page_size=page_size,
                last_evaluated_key=last_evaluated_key
            )
            
            # Yield each item
            for item in result['items']:
                yield item
            
            # Check if there are more results
            last_evaluated_key = result.get('last_evaluated_key')
            if not last_evaluated_key:
                break
    
    def optimized_filter_query(
        self,
        model: Any,
        index_name: str,
        filter_conditions: Dict[str, Any],
        projection_attributes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Use filter expressions and projections for efficient queries"""
        
        # Build filter expression
        filter_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for attr, value in filter_conditions.items():
            if isinstance(value, dict) and 'operator' in value:
                # Handle complex conditions like {'operator': 'begins_with', 'value': 'prefix'}
                operator = value['operator']
                attr_value = value['value']
                
                if operator == 'begins_with':
                    filter_expression_parts.append(f"begins_with(#{attr}, :{attr})")
                elif operator == 'contains':
                    filter_expression_parts.append(f"contains(#{attr}, :{attr})")
                elif operator == 'between':
                    filter_expression_parts.append(f"#{attr} BETWEEN :{attr}_start AND :{attr}_end")
                    expression_attribute_values[f":{attr}_start"] = attr_value[0]
                    expression_attribute_values[f":{attr}_end"] = attr_value[1]
                    continue
                
                expression_attribute_names[f"#{attr}"] = attr
                expression_attribute_values[f":{attr}"] = attr_value
            else:
                # Simple equality condition
                filter_expression_parts.append(f"#{attr} = :{attr}")
                expression_attribute_names[f"#{attr}"] = attr
                expression_attribute_values[f":{attr}"] = value
        
        filter_expression = " AND ".join(filter_expression_parts)
        
        # Build projection expression if specified
        projection_expression = None
        if projection_attributes:
            projection_expression = ", ".join([f"#{attr}" for attr in projection_attributes])
            for attr in projection_attributes:
                expression_attribute_names[f"#{attr}"] = attr
        
        result = self.db.query_by_criteria(
            model=model,
            index_name=index_name,
            table_name=self.table_name,
            filter_expression=filter_expression,
            expression_attribute_values=expression_attribute_values,
            expression_attribute_names=expression_attribute_names,
            projection_expression=projection_expression,
            do_projections=False  # We're handling projections manually
        )
        
        return result.get('Items', [])
```

### 4. Caching Strategies

**Pattern**: Implement multi-layer caching to reduce DynamoDB read operations and improve response times.

**Implementation**:
```python
import json
import time
from typing import Optional, Dict, Any, Union
from functools import wraps

class CacheService:
    """Multi-layer caching service for DynamoDB operations"""
    
    def __init__(self):
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes default TTL
    
    def get_cache_key(self, table_name: str, key: Dict[str, Any]) -> str:
        """Generate consistent cache key"""
        key_str = json.dumps(key, sort_keys=True)
        return f"{table_name}:{hash(key_str)}"
    
    def get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get item from memory cache with TTL check"""
        if cache_key in self.memory_cache:
            cached_item = self.memory_cache[cache_key]
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['data']
            else:
                # Remove expired item
                del self.memory_cache[cache_key]
        return None
    
    def set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Store item in memory cache with timestamp"""
        self.memory_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def invalidate_cache(self, cache_key: str) -> None:
        """Remove item from cache"""
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]

def cached_dynamodb_operation(cache_service: CacheService, ttl: int = 300):
    """Decorator for caching DynamoDB operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key based on function arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache first
            cached_result = cache_service.get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute the actual function
            result = func(self, *args, **kwargs)
            
            # Cache the result
            cache_service.set_cache(cache_key, result)
            
            return result
        return wrapper
    return decorator

# Usage example
cache_service = CacheService()

class CachedUserService:
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name
    
    @cached_dynamodb_operation(cache_service, ttl=600)  # 10 minute cache
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with caching"""
        # This will be cached automatically
        user = User(id=user_id)
        result = self.db.get(model=user, table_name=self.table_name)
        return result.get('Item')
```

## Monitoring & Observability Patterns

### 1. Structured Logging Pattern

**Pattern**: Implement consistent, structured logging across all services for better observability and debugging.

**Implementation**:
```python
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional
from functools import wraps

class StructuredLogger:
    """Structured logging service for consistent log format"""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Configure JSON formatter
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _create_log_entry(
        self, 
        level: str, 
        message: str, 
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create structured log entry"""
        return {
            "timestamp": time.time(),
            "level": level,
            "service": self.service_name,
            "message": message,
            "correlation_id": correlation_id,
            "data": kwargs
        }
    
    def info(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        log_entry = self._create_log_entry("INFO", message, correlation_id, **kwargs)
        self.logger.info(json.dumps(log_entry))
    
    def error(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        log_entry = self._create_log_entry("ERROR", message, correlation_id, **kwargs)
        self.logger.error(json.dumps(log_entry))
    
    def warn(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        log_entry = self._create_log_entry("WARN", message, correlation_id, **kwargs)
        self.logger.warning(json.dumps(log_entry))

def log_service_operation(logger: StructuredLogger):
    """Decorator for automatic service operation logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            correlation_id = kwargs.get('correlation_id', str(uuid.uuid4()))
            operation_name = f"{self.__class__.__name__}.{func.__name__}"
            
            start_time = time.time()
            
            logger.info(
                f"Starting {operation_name}",
                correlation_id=correlation_id,
                operation=operation_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                result = func(self, *args, **kwargs)
                
                duration = time.time() - start_time
                logger.info(
                    f"Completed {operation_name}",
                    correlation_id=correlation_id,
                    operation=operation_name,
                    duration_ms=round(duration * 1000, 2),
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Failed {operation_name}",
                    correlation_id=correlation_id,
                    operation=operation_name,
                    duration_ms=round(duration * 1000, 2),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    success=False
                )
                raise
                
        return wrapper
    return decorator

# Usage example
logger = StructuredLogger("UserService")

class LoggedUserService:
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name
    
    @log_service_operation(logger)
    def create_user(self, user_data: Dict[str, Any], correlation_id: Optional[str] = None):
        """Create user with automatic logging"""
        # Service implementation
        pass
```

### 2. Metrics Collection Pattern

**Pattern**: Collect and track business and technical metrics for performance monitoring and alerting.

**Implementation**:
```python
import time
from typing import Dict, Any, Optional
from enum import Enum

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class MetricsCollector:
    """Metrics collection service for DynamoDB operations"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.metrics: Dict[str, Any] = {}
    
    def increment_counter(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = f"{self.service_name}.{metric_name}"
        if key not in self.metrics:
            self.metrics[key] = {"type": MetricType.COUNTER, "value": 0, "tags": tags or {}}
        self.metrics[key]["value"] += value
    
    def set_gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric value"""
        key = f"{self.service_name}.{metric_name}"
        self.metrics[key] = {"type": MetricType.GAUGE, "value": value, "tags": tags or {}}
    
    def record_timer(self, metric_name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timing metric"""
        key = f"{self.service_name}.{metric_name}"
        if key not in self.metrics:
            self.metrics[key] = {"type": MetricType.TIMER, "values": [], "tags": tags or {}}
        self.metrics[key]["values"].append(duration_ms)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self.metrics

def track_performance_metrics(metrics_collector: MetricsCollector):
    """Decorator for tracking performance metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            operation_name = f"{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(self, *args, **kwargs)
                
                # Record success metrics
                duration = (time.time() - start_time) * 1000
                metrics_collector.record_timer(f"{operation_name}.duration", duration)
                metrics_collector.increment_counter(f"{operation_name}.success")
                
                return result
                
            except Exception as e:
                # Record error metrics
                metrics_collector.increment_counter(
                    f"{operation_name}.error", 
                    tags={"error_type": type(e).__name__}
                )
                raise
                
        return wrapper
    return decorator

# DynamoDB-specific metrics
class DynamoDBMetrics:
    """DynamoDB-specific metrics collection"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    def record_read_capacity(self, consumed_capacity: float, table_name: str):
        """Record DynamoDB read capacity consumption"""
        self.metrics.set_gauge(
            "dynamodb.read_capacity_consumed",
            consumed_capacity,
            tags={"table": table_name}
        )
    
    def record_write_capacity(self, consumed_capacity: float, table_name: str):
        """Record DynamoDB write capacity consumption"""
        self.metrics.set_gauge(
            "dynamodb.write_capacity_consumed",
            consumed_capacity,
            tags={"table": table_name}
        )
    
    def record_item_count(self, count: int, operation: str, table_name: str):
        """Record number of items processed"""
        self.metrics.increment_counter(
            "dynamodb.items_processed",
            count,
            tags={"operation": operation, "table": table_name}
        )
```

### 3. Health Check Patterns

**Pattern**: Implement comprehensive health checks for service dependencies and system status.

**Implementation**:
```python
from typing import Dict, Any, List
import time
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck:
    """Individual health check implementation"""
    
    def __init__(self, name: str, check_function, timeout: int = 5):
        self.name = name
        self.check_function = check_function
        self.timeout = timeout
    
    def execute(self) -> Dict[str, Any]:
        """Execute health check with timeout"""
        start_time = time.time()
        
        try:
            result = self.check_function()
            duration = time.time() - start_time
            
            return {
                "name": self.name,
                "status": HealthStatus.HEALTHY.value,
                "duration_ms": round(duration * 1000, 2),
                "details": result
            }
            
        except Exception as e:
            duration = time.time() - start_time
            
            return {
                "name": self.name,
                "status": HealthStatus.UNHEALTHY.value,
                "duration_ms": round(duration * 1000, 2),
                "error": str(e)
            }

class HealthCheckService:
    """Service for managing and executing health checks"""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
    
    def add_check(self, health_check: HealthCheck):
        """Add a health check"""
        self.checks.append(health_check)
    
    def execute_all_checks(self) -> Dict[str, Any]:
        """Execute all health checks and return aggregated status"""
        results = []
        overall_status = HealthStatus.HEALTHY
        
        for check in self.checks:
            result = check.execute()
            results.append(result)
            
            if result["status"] == HealthStatus.UNHEALTHY.value:
                overall_status = HealthStatus.UNHEALTHY
            elif result["status"] == HealthStatus.DEGRADED.value and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "checks": results,
            "summary": {
                "total": len(results),
                "healthy": len([r for r in results if r["status"] == HealthStatus.HEALTHY.value]),
                "degraded": len([r for r in results if r["status"] == HealthStatus.DEGRADED.value]),
                "unhealthy": len([r for r in results if r["status"] == HealthStatus.UNHEALTHY.value])
            }
        }

# DynamoDB health checks
def create_dynamodb_health_checks(db: DynamoDB, table_name: str) -> List[HealthCheck]:
    """Create DynamoDB-specific health checks"""
    
    def check_table_exists():
        """Check if DynamoDB table exists and is active"""
        try:
            response = db.client.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            
            if status == 'ACTIVE':
                return {"table_status": status, "item_count": response['Table']['ItemCount']}
            else:
                raise Exception(f"Table status is {status}, expected ACTIVE")
                
        except Exception as e:
            raise Exception(f"Table check failed: {str(e)}")
    
    def check_read_write_capacity():
        """Check DynamoDB read/write capacity"""
        try:
            # Perform a simple read operation
            test_key = {"pk": "health_check", "sk": "health_check"}
            db.client.get_item(TableName=table_name, Key=test_key)
            
            return {"read_test": "success"}
            
        except Exception as e:
            raise Exception(f"Capacity check failed: {str(e)}")
    
    return [
        HealthCheck("dynamodb_table_status", check_table_exists),
        HealthCheck("dynamodb_read_capacity", check_read_write_capacity)
    ]
```

## Security Enhancement Patterns

### 1. Field-Level Encryption Pattern

**Pattern**: Encrypt sensitive data fields before storing in DynamoDB while maintaining queryability for non-sensitive fields.

**Implementation**:
```python
import boto3
from cryptography.fernet import Fernet
from typing import Dict, Any, Optional

class FieldEncryption:
    """Field-level encryption for sensitive data"""
    
    def __init__(self, kms_key_id: Optional[str] = None):
        self.kms_client = boto3.client('kms')
        self.kms_key_id = kms_key_id
        self._encryption_key = None
    
    def get_encryption_key(self) -> bytes:
        """Get or generate encryption key using KMS"""
        if self._encryption_key is None:
            if self.kms_key_id:
                # Use KMS to generate data key
                response = self.kms_client.generate_data_key(
                    KeyId=self.kms_key_id,
                    KeySpec='AES_256'
                )
                self._encryption_key = response['Plaintext']
            else:
                # Generate local key (for development only)
                self._encryption_key = Fernet.generate_key()
        
        return self._encryption_key
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a field value"""
        if not value:
            return value
        
        fernet = Fernet(self.get_encryption_key())
        encrypted_bytes = fernet.encrypt(value.encode())
        return encrypted_bytes.decode()
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a field value"""
        if not encrypted_value:
            return encrypted_value
        
        fernet = Fernet(self.get_encryption_key())
        decrypted_bytes = fernet.decrypt(encrypted_value.encode())
        return decrypted_bytes.decode()

class SecureUserModel(DynamoDBModelBase):
    """User model with field-level encryption"""
    
    def __init__(self):
        super().__init__()
        self.id: str = ""
        self.email: str = ""  # Will be encrypted
        self.name: str = ""
        self.phone: str = ""  # Will be encrypted
        self.encrypted_fields = ['email', 'phone']
        self.encryption_service = FieldEncryption()
    
    def encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        for field in self.encrypted_fields:
            if hasattr(self, field):
                value = getattr(self, field)
                if value:
                    encrypted_value = self.encryption_service.encrypt_field(value)
                    setattr(self, f"encrypted_{field}", encrypted_value)
                    # Clear the original field
                    setattr(self, field, "")
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields after loading"""
        for field in self.encrypted_fields:
            encrypted_field = f"encrypted_{field}"
            if hasattr(self, encrypted_field):
                encrypted_value = getattr(self, encrypted_field)
                if encrypted_value:
                    decrypted_value = self.encryption_service.decrypt_field(encrypted_value)
                    setattr(self, field, decrypted_value)
```

### 2. Audit Logging Pattern

**Pattern**: Comprehensive audit trail for all data changes with immutable logging.

**Implementation**:
```python
import json
from typing import Dict, Any, Optional
from enum import Enum

class AuditAction(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"

class AuditLog(DynamoDBModelBase):
    """Immutable audit log entry"""
    
    def __init__(self):
        super().__init__()
        self.audit_id: str = StringUtility.generate_sortable_uuid()
        self.entity_type: str = ""
        self.entity_id: str = ""
        self.action: str = ""
        self.user_id: str = ""
        self.tenant_id: str = ""
        self.timestamp: str = ""
        self.old_values: Optional[Dict[str, Any]] = None
        self.new_values: Optional[Dict[str, Any]] = None
        self.ip_address: Optional[str] = None
        self.user_agent: Optional[str] = None
        self._setup_audit_indexes()
    
    def _setup_audit_indexes(self):
        """Setup indexes for audit queries"""
        # Primary key: audit_id
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: f"audit#{self.audit_id}"
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: f"audit#{self.audit_id}"
        self.indexes.add_primary(primary)
        
        # GSI1: Entity-based queries
        gsi1 = DynamoDBIndex(index_name="gsi1")
        gsi1.partition_key.attribute_name = "gsi1_pk"
        gsi1.partition_key.value = lambda: f"entity#{self.entity_type}#{self.entity_id}"
        gsi1.sort_key.attribute_name = "gsi1_sk"
        gsi1.sort_key.value = lambda: f"timestamp#{self.timestamp}"
        self.indexes.add_secondary(gsi1)

class AuditService:
    """Service for managing audit logs"""
    
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name
    
    def log_action(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        user_id: str,
        tenant_id: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Create audit log entry"""
        audit_log = AuditLog()
        audit_log.entity_type = entity_type
        audit_log.entity_id = entity_id
        audit_log.action = action.value
        audit_log.user_id = user_id
        audit_log.tenant_id = tenant_id
        audit_log.timestamp = str(int(time.time()))
        audit_log.old_values = old_values
        audit_log.new_values = new_values
        
        if context:
            audit_log.ip_address = context.get('ip_address')
            audit_log.user_agent = context.get('user_agent')
        
        # Save audit log (immutable)
        self.db.save(
            item=audit_log.to_resource_dictionary(),
            table_name=self.table_name
        )

def audit_data_changes(audit_service: AuditService):
    """Decorator for automatic audit logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Extract audit context
            entity_id = kwargs.get('id') or (args[0] if args else None)
            user_id = kwargs.get('user_id', 'system')
            tenant_id = kwargs.get('tenant_id', 'default')
            
            # Get old values for updates
            old_values = None
            if func.__name__ in ['update', 'delete'] and entity_id:
                try:
                    old_item = self.get_by_id(entity_id, tenant_id, user_id)
                    if old_item.success:
                        old_values = old_item.data.to_dictionary()
                except:
                    pass
            
            # Execute the operation
            result = func(self, *args, **kwargs)
            
            # Log the action if successful
            if hasattr(result, 'success') and result.success:
                action_map = {
                    'create': AuditAction.CREATE,
                    'update': AuditAction.UPDATE,
                    'delete': AuditAction.DELETE
                }
                
                action = action_map.get(func.__name__)
                if action:
                    new_values = None
                    if hasattr(result, 'data') and result.data:
                        new_values = result.data.to_dictionary()
                    
                    audit_service.log_action(
                        action=action,
                        entity_type=self.__class__.__name__.replace('Service', '').lower(),
                        entity_id=str(entity_id),
                        user_id=user_id,
                        tenant_id=tenant_id,
                        old_values=old_values,
                        new_values=new_values
                    )
            
            return result
        return wrapper
    return decorator
```

## Migration & Evolution Patterns

### 1. Schema Evolution Pattern

**Pattern**: Handle DynamoDB schema changes without downtime using versioned models and backward compatibility.

**Implementation**:
```python
from typing import Dict, Any, Optional
from enum import Enum

class ModelVersion(Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"

class VersionedModel(DynamoDBModelBase):
    """Base class for versioned models"""
    
    def __init__(self):
        super().__init__()
        self.model_version: str = ModelVersion.V3.value  # Current version
        self.migration_status: Optional[str] = None
    
    def migrate_from_version(self, old_data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Migrate data from older version to current version"""
        migrated_data = old_data.copy()
        
        if from_version == ModelVersion.V1.value:
            migrated_data = self._migrate_v1_to_v2(migrated_data)
            migrated_data = self._migrate_v2_to_v3(migrated_data)
        elif from_version == ModelVersion.V2.value:
            migrated_data = self._migrate_v2_to_v3(migrated_data)
        
        migrated_data['model_version'] = ModelVersion.V3.value
        return migrated_data
    
    def _migrate_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migration logic from v1 to v2"""
        # Example: rename field
        if 'old_field_name' in data:
            data['new_field_name'] = data.pop('old_field_name')
        return data
    
    def _migrate_v2_to_v3(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migration logic from v2 to v3"""
        # Example: add new required field with default
        if 'new_required_field' not in data:
            data['new_required_field'] = 'default_value'
        return data

class MigrationService:
    """Service for handling data migrations"""
    
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name
    
    def migrate_item(self, item: Dict[str, Any], target_model_class) -> Dict[str, Any]:
        """Migrate a single item to the latest version"""
        current_version = item.get('model_version', ModelVersion.V1.value)
        
        if current_version != ModelVersion.V3.value:
            # Create instance of target model
            model_instance = target_model_class()
            
            # Perform migration
            migrated_data = model_instance.migrate_from_version(item, current_version)
            
            # Update the item in DynamoDB
            self.db.save(item=migrated_data, table_name=self.table_name)
            
            return migrated_data
        
        return item
    
    def batch_migrate_items(self, model_class, batch_size: int = 25):
        """Migrate all items of a specific model type"""
        # Scan for items that need migration
        scan_params = {
            'table_name': self.table_name,
            'filter_expression': 'model_version <> :current_version',
            'expression_attribute_values': {
                ':current_version': ModelVersion.V3.value
            }
        }
        
        items_to_migrate = []
        response = self.db.client.scan(**scan_params)
        
        for item in response.get('Items', []):
            migrated_item = self.migrate_item(item, model_class)
            items_to_migrate.append(migrated_item)
            
            # Process in batches
            if len(items_to_migrate) >= batch_size:
                self._process_migration_batch(items_to_migrate)
                items_to_migrate = []
        
        # Process remaining items
        if items_to_migrate:
            self._process_migration_batch(items_to_migrate)
    
    def _process_migration_batch(self, items: List[Dict[str, Any]]):
        """Process a batch of migrated items"""
        # Could implement additional validation, logging, etc.
        pass
```

## Cost Optimization Patterns

### 1. DynamoDB Cost Management

**Pattern**: Optimize DynamoDB costs through efficient access patterns, capacity planning, and data lifecycle management.

**Implementation**:
```python
class CostOptimizedService:
    """Service with cost optimization strategies"""
    
    def __init__(self, db: DynamoDB, table_name: str):
        self.db = db
        self.table_name = table_name
    
    def efficient_batch_operations(self, items: List[Dict[str, Any]]):
        """Use batch operations to reduce request costs"""
        batch_size = 25  # DynamoDB batch limit
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Use batch_write_item instead of individual puts
            request_items = {
                self.table_name: [
                    {'PutRequest': {'Item': item}} for item in batch
                ]
            }
            
            self.db.client.batch_write_item(RequestItems=request_items)
    
    def use_projections_for_cost_savings(self, model, index_name: str):
        """Use projections to reduce data transfer costs"""
        # Only fetch required attributes
        essential_attributes = ['id', 'name', 'status', 'updated_utc']
        
        result = self.db.query_by_criteria(
            model=model,
            index_name=index_name,
            table_name=self.table_name,
            projection_expression=','.join(essential_attributes),
            do_projections=False  # Manual projection control
        )
        
        return result.get('Items', [])
    
    def implement_data_archiving(self, cutoff_date: str):
        """Archive old data to reduce storage costs"""
        # Query old items
        archive_filter = f"updated_utc < :cutoff_date"
        
        old_items = self.db.client.scan(
            TableName=self.table_name,
            FilterExpression=archive_filter,
            ExpressionAttributeValues={':cutoff_date': cutoff_date}
        )
        
        # Move to S3 or delete based on retention policy
        for item in old_items.get('Items', []):
            # Archive to S3 (implementation depends on requirements)
            self._archive_to_s3(item)
            
            # Delete from DynamoDB
            self.db.delete(
                primary_key={'pk': item['pk'], 'sk': item['sk']},
                table_name=self.table_name
            )
```

## Disaster Recovery Patterns

### 1. Backup and Restore Strategy

**Pattern**: Implement comprehensive backup strategies for DynamoDB data with automated recovery procedures.

**Implementation**:
```python
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class BackupService:
    """Service for managing DynamoDB backups and recovery"""
    
    def __init__(self, table_name: str, region: str = 'us-east-1'):
        self.table_name = table_name
        self.region = region
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
    
    def create_point_in_time_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create on-demand backup"""
        if not backup_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{self.table_name}_backup_{timestamp}"
        
        response = self.dynamodb_client.create_backup(
            TableName=self.table_name,
            BackupName=backup_name
        )
        
        return {
            'backup_arn': response['BackupDetails']['BackupArn'],
            'backup_name': backup_name,
            'status': response['BackupDetails']['BackupStatus']
        }
    
    def export_to_s3(self, s3_bucket: str, s3_prefix: str) -> Dict[str, Any]:
        """Export table data to S3 for cross-region backup"""
        export_time = datetime.now()
        
        response = self.dynamodb_client.export_table_to_point_in_time(
            TableArn=f"arn:aws:dynamodb:{self.region}:*:table/{self.table_name}",
            S3Bucket=s3_bucket,
            S3Prefix=s3_prefix,
            ExportFormat='DYNAMODB_JSON',
            ExportTime=export_time
        )
        
        return {
            'export_arn': response['ExportDescription']['ExportArn'],
            'export_status': response['ExportDescription']['ExportStatus'],
            's3_location': f"s3://{s3_bucket}/{s3_prefix}"
        }
    
    def restore_from_backup(self, backup_arn: str, target_table_name: str) -> Dict[str, Any]:
        """Restore table from backup"""
        response = self.dynamodb_client.restore_table_from_backup(
            TargetTableName=target_table_name,
            BackupArn=backup_arn
        )
        
        return {
            'table_arn': response['TableDescription']['TableArn'],
            'restore_status': response['TableDescription']['TableStatus']
        }
    
    def setup_continuous_backups(self) -> Dict[str, Any]:
        """Enable point-in-time recovery"""
        response = self.dynamodb_client.update_continuous_backups(
            TableName=self.table_name,
            PointInTimeRecoverySpecification={'PointInTimeRecoveryEnabled': True}
        )
        
        return {
            'point_in_time_recovery_status': response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus']
        }

class DisasterRecoveryOrchestrator:
    """Orchestrate disaster recovery procedures"""
    
    def __init__(self, primary_region: str, backup_region: str):
        self.primary_region = primary_region
        self.backup_region = backup_region
        self.primary_dynamodb = boto3.client('dynamodb', region_name=primary_region)
        self.backup_dynamodb = boto3.client('dynamodb', region_name=backup_region)
    
    def failover_to_backup_region(self, table_name: str, backup_table_name: str) -> Dict[str, Any]:
        """Execute failover to backup region"""
        try:
            # 1. Verify backup region table is ready
            backup_status = self.backup_dynamodb.describe_table(TableName=backup_table_name)
            
            if backup_status['Table']['TableStatus'] != 'ACTIVE':
                raise Exception(f"Backup table {backup_table_name} is not active")
            
            # 2. Update application configuration to point to backup region
            # This would typically involve updating environment variables or configuration
            
            # 3. Verify data consistency
            primary_count = self._get_table_item_count(self.primary_dynamodb, table_name)
            backup_count = self._get_table_item_count(self.backup_dynamodb, backup_table_name)
            
            return {
                'failover_status': 'success',
                'primary_region': self.primary_region,
                'backup_region': self.backup_region,
                'data_consistency': {
                    'primary_count': primary_count,
                    'backup_count': backup_count,
                    'difference': abs(primary_count - backup_count)
                }
            }
            
        except Exception as e:
            return {
                'failover_status': 'failed',
                'error': str(e)
            }
    
    def _get_table_item_count(self, client, table_name: str) -> int:
        """Get approximate item count from table"""
        response = client.describe_table(TableName=table_name)
        return response['Table']['ItemCount']
```

### 2. Cross-Region Replication

**Pattern**: Implement cross-region data replication for high availability and disaster recovery.

**Implementation**:
```python
class CrossRegionReplication:
    """Manage cross-region replication for disaster recovery"""
    
    def __init__(self, source_region: str, target_regions: List[str]):
        self.source_region = source_region
        self.target_regions = target_regions
        self.source_client = boto3.client('dynamodb', region_name=source_region)
    
    def setup_global_tables(self, table_name: str) -> Dict[str, Any]:
        """Setup DynamoDB Global Tables for automatic replication"""
        try:
            # Create global table
            replica_regions = [{'RegionName': region} for region in self.target_regions]
            
            response = self.source_client.create_global_table(
                GlobalTableName=table_name,
                ReplicationGroup=replica_regions
            )
            
            return {
                'global_table_arn': response['GlobalTableDescription']['GlobalTableArn'],
                'global_table_status': response['GlobalTableDescription']['GlobalTableStatus'],
                'replicas': response['GlobalTableDescription']['ReplicationGroup']
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def monitor_replication_lag(self, table_name: str) -> Dict[str, Any]:
        """Monitor replication lag across regions"""
        replication_metrics = {}
        
        for region in self.target_regions:
            client = boto3.client('dynamodb', region_name=region)
            
            try:
                response = client.describe_table(TableName=table_name)
                replication_metrics[region] = {
                    'status': response['Table']['TableStatus'],
                    'item_count': response['Table']['ItemCount'],
                    'last_updated': response['Table'].get('TableCreationDateTime')
                }
            except Exception as e:
                replication_metrics[region] = {'error': str(e)}
        
        return replication_metrics
```

## API Versioning Patterns

### 1. Backward Compatible API Evolution

**Pattern**: Implement API versioning strategies that maintain backward compatibility while allowing for evolution.

**Implementation**:
```python
from typing import Dict, Any, Optional
from enum import Enum

class APIVersion(Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"

class VersionedAPIHandler:
    """Handle multiple API versions with backward compatibility"""
    
    def __init__(self):
        self.supported_versions = [APIVersion.V1, APIVersion.V2, APIVersion.V3]
        self.default_version = APIVersion.V3
    
    def get_api_version(self, event: Dict[str, Any]) -> APIVersion:
        """Extract API version from request"""
        # Check headers first
        headers = event.get('headers', {})
        version_header = headers.get('API-Version') or headers.get('api-version')
        
        if version_header:
            try:
                return APIVersion(version_header)
            except ValueError:
                pass
        
        # Check path parameter
        path_parameters = event.get('pathParameters', {})
        version_path = path_parameters.get('version')
        
        if version_path:
            try:
                return APIVersion(version_path)
            except ValueError:
                pass
        
        # Default to latest version
        return self.default_version
    
    def transform_request(self, request_data: Dict[str, Any], from_version: APIVersion, to_version: APIVersion) -> Dict[str, Any]:
        """Transform request data between API versions"""
        if from_version == to_version:
            return request_data
        
        transformed_data = request_data.copy()
        
        # V1 to V2 transformations
        if from_version == APIVersion.V1 and to_version in [APIVersion.V2, APIVersion.V3]:
            # Example: rename field
            if 'oldFieldName' in transformed_data:
                transformed_data['newFieldName'] = transformed_data.pop('oldFieldName')
        
        # V2 to V3 transformations
        if from_version in [APIVersion.V1, APIVersion.V2] and to_version == APIVersion.V3:
            # Example: add required field with default
            if 'requiredNewField' not in transformed_data:
                transformed_data['requiredNewField'] = 'default_value'
        
        return transformed_data
    
    def transform_response(self, response_data: Dict[str, Any], from_version: APIVersion, to_version: APIVersion) -> Dict[str, Any]:
        """Transform response data to match requested API version"""
        if from_version == to_version:
            return response_data
        
        transformed_data = response_data.copy()
        
        # V3 to V2 transformations (backward compatibility)
        if from_version == APIVersion.V3 and to_version == APIVersion.V2:
            # Remove fields that don't exist in V2
            transformed_data.pop('newV3Field', None)
        
        # V3/V2 to V1 transformations
        if from_version in [APIVersion.V2, APIVersion.V3] and to_version == APIVersion.V1:
            # Rename fields back to V1 format
            if 'newFieldName' in transformed_data:
                transformed_data['oldFieldName'] = transformed_data.pop('newFieldName')
            
            # Remove fields that don't exist in V1
            transformed_data.pop('newV2Field', None)
            transformed_data.pop('newV3Field', None)
        
        return transformed_data

def versioned_api_handler(handler_func):
    """Decorator for handling API versioning"""
    def wrapper(event, context, injected_services=None):
        versioned_handler = VersionedAPIHandler()
        
        # Determine API version
        requested_version = versioned_handler.get_api_version(event)
        current_version = APIVersion.V3  # The version your handler implements
        
        # Transform request if needed
        if 'body' in event and event['body']:
            body = json.loads(event['body'])
            transformed_body = versioned_handler.transform_request(
                body, requested_version, current_version
            )
            event['body'] = json.dumps(transformed_body)
        
        # Execute the handler
        response = handler_func(event, context, injected_services)
        
        # Transform response if needed
        if response.get('body'):
            response_body = json.loads(response['body'])
            if 'data' in response_body:
                transformed_data = versioned_handler.transform_response(
                    response_body['data'], current_version, requested_version
                )
                response_body['data'] = transformed_data
                response['body'] = json.dumps(response_body)
        
        # Add version header to response
        if 'headers' not in response:
            response['headers'] = {}
        response['headers']['API-Version'] = requested_version.value
        
        return response
    
    return wrapper

# Usage example
@versioned_api_handler
def lambda_handler(event, context, injected_services=None):
    """Lambda handler with automatic API versioning"""
    # Your handler implementation here
    # This will receive the transformed request and return transformed response
    pass
```

### 2. Schema Validation by Version

**Pattern**: Implement version-specific schema validation to ensure API contracts are maintained.

**Implementation**:
```python
from jsonschema import validate, ValidationError
from typing import Dict, Any

class APISchemaValidator:
    """Validate API requests and responses by version"""
    
    def __init__(self):
        self.schemas = {
            APIVersion.V1: {
                'request': {
                    'type': 'object',
                    'properties': {
                        'oldFieldName': {'type': 'string'},
                        'commonField': {'type': 'string'}
                    },
                    'required': ['oldFieldName']
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'oldFieldName': {'type': 'string'},
                        'commonField': {'type': 'string'}
                    }
                }
            },
            APIVersion.V2: {
                'request': {
                    'type': 'object',
                    'properties': {
                        'newFieldName': {'type': 'string'},
                        'commonField': {'type': 'string'},
                        'newV2Field': {'type': 'string'}
                    },
                    'required': ['newFieldName']
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'newFieldName': {'type': 'string'},
                        'commonField': {'type': 'string'},
                        'newV2Field': {'type': 'string'}
                    }
                }
            },
            APIVersion.V3: {
                'request': {
                    'type': 'object',
                    'properties': {
                        'newFieldName': {'type': 'string'},
                        'commonField': {'type': 'string'},
                        'newV2Field': {'type': 'string'},
                        'requiredNewField': {'type': 'string'},
                        'newV3Field': {'type': 'string'}
                    },
                    'required': ['newFieldName', 'requiredNewField']
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'newFieldName': {'type': 'string'},
                        'commonField': {'type': 'string'},
                        'newV2Field': {'type': 'string'},
                        'requiredNewField': {'type': 'string'},
                        'newV3Field': {'type': 'string'}
                    }
                }
            }
        }
    
    def validate_request(self, data: Dict[str, Any], version: APIVersion) -> bool:
        """Validate request data against version schema"""
        try:
            schema = self.schemas[version]['request']
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            raise ValueError(f"Request validation failed for {version.value}: {e.message}")
    
    def validate_response(self, data: Dict[str, Any], version: APIVersion) -> bool:
        """Validate response data against version schema"""
        try:
            schema = self.schemas[version]['response']
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            raise ValueError(f"Response validation failed for {version.value}: {e.message}")
```

## Configuration Management

### 1. Multi-Environment Support

**Pattern**: Environment-specific configuration with template substitution.

**Template Variables**:
- `{{ENVIRONMENT}}` → dev/staging/prod
- `{{ORGANIZATION_NAME}}` → your-organization
- `{resource_name}` → specific resource names

### 2. Configuration Validation

**Pattern**: Comprehensive validation of configuration files and SSM parameters.

**Validation Areas**:
- SSM parameter path format validation
- Environment variable naming consistency
- Cross-stack parameter reference validation
- Template variable substitution validation

### 3. Backward Compatibility

**Pattern**: Support both legacy and new configuration formats.

**Implementation**:
- Support both "ssm" and "enhanced_ssm" field names
- Environment variable fallback chains
- Graceful degradation for missing parameters

## Best Practices Summary

1. **Consistency**: Use standardized patterns across all components
2. **Separation of Concerns**: Clear layer boundaries with specific responsibilities
3. **Testability**: Dependency injection and mocking support throughout
4. **Scalability**: Single table design with efficient indexing strategies
5. **Maintainability**: Automatic code generation and convention-based naming
6. **Security**: Tenant isolation and proper authentication/authorization
7. **Performance**: Lazy loading and efficient DynamoDB access patterns
8. **Flexibility**: Configuration-driven behavior with environment-specific settings

## Usage in Other Projects

To implement these patterns in a new project:

1. **Setup Virtual Environment** (CRITICAL):
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate
   ```
   
   **Why Virtual Environments are Essential**:
   - **Dependency Isolation**: Prevents conflicts between project dependencies
   - **Reproducible Builds**: Ensures consistent package versions across environments
   - **Clean Development**: Avoids polluting system Python installation
   - **Team Consistency**: All developers use identical dependency versions
   - **Deployment Safety**: Production environments match development exactly
   
   **Standard Practice**: Always use `.venv` as the virtual environment directory name for consistency across all projects.

2. **Install Dependencies**:
   ```bash
   pip install boto3-assist
   ```

3. **Create Base Models**:
   - Inherit from `DynamoDBModelBase`
   - Implement tenant-based models if multi-tenant
   - Add automatic case conversion methods

4. **Implement Service Layer**:
   - Create service factory for dependency management
   - Follow standard CRUD + business logic pattern
   - Use ServiceResult for consistent responses

5. **Setup Lambda Handlers**:
   - Use decorator-based middleware
   - Implement service injection pattern
   - Add automatic request/response transformation

6. **Configure Infrastructure**:
   - Setup SSM parameter integration
   - Use standardized environment variables
   - Implement CDK integration patterns

These design patterns provide a robust, scalable foundation for AWS-based SaaS applications with DynamoDB as the primary data store.
