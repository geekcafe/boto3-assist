# boto3-assist Decimal Handling: Before & After

> **Status**: 📋 Proposed Enhancement - Pending Implementation  
> **Last Updated**: 2025-10-12  
> **TODO**: Update examples once boto3-assist implements this feature

---

## The Problem: Real-World Example

### Before Enhancement (Current State)

```python
# Model definition
class VoteSummary(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._choice_averages: Dict[str, float] = {}
    
    @property
    def choice_averages(self) -> Dict[str, float]:
        # ⚠️ PROBLEM: Must convert Decimals manually
        return {k: float(v) if isinstance(v, Decimal) else v 
                for k, v in self._choice_averages.items()}
    
    @choice_averages.setter
    def choice_averages(self, value: Dict[str, float]):
        self._choice_averages = value


# Application code
def test_vote_averages():
    # Save
    summary = VoteSummary()
    summary.choice_averages = {"product_a": 4.5}
    db.save(table_name="summaries", item=summary)
    
    # Retrieve
    result = db.get(table_name="summaries", key={...})
    retrieved = VoteSummary().map(result)
    
    # ❌ PROBLEM: This fails with TypeError!
    # TypeError: unsupported operand type(s) for -: 'decimal.Decimal' and 'float'
    assert abs(retrieved.choice_averages["product_a"] - 4.5) < 0.1
    
    # 😞 WORKAROUND: Must remember to convert manually
    assert abs(float(retrieved.choice_averages["product_a"]) - 4.5) < 0.1
```

**Issues:**
1. ❌ Manual Decimal conversion in property getter breaks `.map()` (loses data)
2. ❌ OR developers must remember `float()` everywhere
3. ❌ TypeErrors occur in production when forgotten
4. ❌ Code is cluttered with type conversions

---

### After Enhancement (Proposed State)

```python
# Model definition
class VoteSummary(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._choice_averages: Dict[str, float] = {}  # Type hint is key!
    
    @property
    def choice_averages(self) -> Dict[str, float]:
        # ✅ SOLUTION: Just return it - boto3-assist handles conversion!
        return self._choice_averages
    
    @choice_averages.setter
    def choice_averages(self, value: Dict[str, float]):
        self._choice_averages = value


# Application code
def test_vote_averages():
    # Save
    summary = VoteSummary()
    summary.choice_averages = {"product_a": 4.5}
    db.save(table_name="summaries", item=summary)
    
    # Retrieve
    result = db.get(table_name="summaries", key={...})
    retrieved = VoteSummary().map(result)
    
    # ✅ WORKS: Decimals automatically converted during .map()!
    assert abs(retrieved.choice_averages["product_a"] - 4.5) < 0.1
    
    # ✅ Type is correct
    assert isinstance(retrieved.choice_averages["product_a"], float)
    
    # ✅ Arithmetic operations just work
    if retrieved.choice_averages["product_a"] > 4.0:
        print("High rating!")
```

**Benefits:**
1. ✅ No manual conversion needed anywhere
2. ✅ Type hints drive behavior (Pythonic!)
3. ✅ No TypeErrors in production
4. ✅ Clean, readable code

---

## More Examples

### Example 1: Direct Float Property

#### Before
```python
class Analytics(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._conversion_rate: float = 0.0
    
    @property
    def conversion_rate(self) -> float:
        # Must handle Decimal
        if isinstance(self._conversion_rate, Decimal):
            return float(self._conversion_rate)
        return self._conversion_rate
    
    @conversion_rate.setter
    def conversion_rate(self, value: float):
        self._conversion_rate = value

# Usage
analytics = Analytics().map(result)
rate = float(analytics.conversion_rate)  # Still need this sometimes!
```

#### After
```python
class Analytics(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._conversion_rate: float = 0.0  # Type hint!
    
    @property
    def conversion_rate(self) -> float:
        return self._conversion_rate  # Just return it!
    
    @conversion_rate.setter
    def conversion_rate(self, value: float):
        self._conversion_rate = value

# Usage
analytics = Analytics().map(result)
rate = analytics.conversion_rate  # Already a float!
```

---

### Example 2: List of Floats

#### Before
```python
class Metrics(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._scores: List[float] = []
    
    @property
    def scores(self) -> List[float]:
        # Convert all Decimals to float
        return [float(x) if isinstance(x, Decimal) else x for x in self._scores]
    
    @scores.setter
    def scores(self, value: List[float]):
        self._scores = value

# Usage
metrics = Metrics().map(result)
avg = sum(metrics.scores) / len(metrics.scores)  # Works, but scores is a NEW list each time
```

#### After
```python
class Metrics(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._scores: List[float] = []  # Type hint!
    
    @property
    def scores(self) -> List[float]:
        return self._scores  # boto3-assist converted it already!
    
    @scores.setter
    def scores(self, value: List[float]):
        self._scores = value

# Usage  
metrics = Metrics().map(result)
avg = sum(metrics.scores) / len(metrics.scores)  # Cleaner and faster!
```

---

### Example 3: Complex Nested Structure

#### Before
```python
class Report(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._metrics: Dict[str, Any] = {}
    
    @property
    def metrics(self) -> Dict[str, Any]:
        # Recursive Decimal conversion
        def convert(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            return obj
        return convert(self._metrics)  # NEW object every call!
    
    @metrics.setter
    def metrics(self, value: Dict[str, Any]):
        self._metrics = value

# Usage
report = Report().map(result)
# Sometimes works, sometimes doesn't depending on when .map() was called!
avg_load_time = report.metrics["performance"]["avg_load_time_ms"]
# Still might need: float(avg_load_time)
```

#### After
```python
class Report(DynamoDBModelBase):
    def __init__(self):
        super().__init__()
        self._metrics: Dict[str, Any] = {}  # Even with Any!
    
    @property
    def metrics(self) -> Dict[str, Any]:
        return self._metrics  # boto3-assist handled it during .map()!
    
    @metrics.setter
    def metrics(self, value: Dict[str, Any]):
        self._metrics = value

# Usage
report = Report().map(result)
# Just works - all nested Decimals converted to float!
avg_load_time = report.metrics["performance"]["avg_load_time_ms"]
if avg_load_time < 200:
    print("Fast!")
```

---

## The Key Insight

### The Problem Wasn't the Conversion Logic

The problem was **WHERE** the conversion happened:

❌ **Wrong**: Property getter creates new object → breaks `.map()` → data loss  
✅ **Right**: `.map()` method converts during deserialization → preserves object identity

### The Solution: Type-Driven Conversion

Let Python's type hints tell boto3-assist what you want:

```python
self._value: float = 0.0           # → boto3-assist converts Decimal to float
self._count: int = 0               # → boto3-assist converts Decimal to int  
self._rates: Dict[str, float] = {} # → boto3-assist converts nested Decimals
self._raw: Any = None              # → boto3-assist converts Decimals to float (convenience)
```

---

## Migration Guide for Existing Code

### Step 1: Identify Properties with Decimal Issues
Look for:
- Properties that do manual Decimal conversion in getters
- Code that calls `float()` on retrieved values
- Tests with `TypeError: unsupported operand type(s)`

### Step 2: Simplify Property Definitions
**Remove conversion logic from getters:**
```python
# Before
@property
def content(self) -> Dict[str, Any]:
    return self._convert_decimals(self._content)  # ❌ Remove this

# After  
@property
def content(self) -> Dict[str, Any]:
    return self._content  # ✅ Just return it
```

### Step 3: Add Type Hints (if missing)
```python
# Before
def __init__(self):
    super().__init__()
    self._scores = []  # ❌ No type hint

# After
def __init__(self):
    super().__init__()
    self._scores: List[float] = []  # ✅ Type hint added
```

### Step 4: Remove Manual float() Conversions
```python
# Before
assert abs(float(summary.average) - 4.5) < 0.1  # ❌ Unnecessary

# After
assert abs(summary.average - 4.5) < 0.1  # ✅ Cleaner
```

### Step 5: Test Thoroughly
- Run full test suite
- Check arithmetic operations work
- Verify save/retrieve round trips
- Ensure backward compatibility

---

## FAQ

**Q: What if I need the raw Decimal for precision?**  
A: Don't add a type hint, or use `Decimal` as the type hint. Without a hint, boto3-assist preserves the Decimal.

**Q: Does this work with nested structures?**  
A: Yes! `Dict[str, Dict[str, float]]` and `List[List[float]]` are supported.

**Q: What about performance?**  
A: Minimal overhead. Type hint lookup is cached, conversion is O(n) same as manual conversion.

**Q: Is this backward compatible?**  
A: Yes! Properties without type hints preserve current behavior.

**Q: What if I have Dict[str, Any]?**  
A: Nested Decimals are converted to float by default for convenience (prevents common errors).

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Property Code** | Complex conversion logic | Simple return statement |
| **Application Code** | Manual `float()` everywhere | Direct usage |
| **Type Safety** | Runtime errors | Type hints + auto-conversion |
| **Maintainability** | Error-prone | Clean and obvious |
| **Developer Experience** | Frustrating | Delightful! |

**Result: boto3-assist becomes the easiest way to work with DynamoDB in Python!** 🎯
