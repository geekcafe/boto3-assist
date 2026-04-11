# Requirements Document

## Introduction

Add an optional `keys` parameter to the `to_dict` and `to_dictionary` methods on `DynamoDBModelBase`. When provided, the returned dictionary is filtered to include only the specified top-level keys. This enables callers to extract lightweight, purpose-specific dictionaries from model instances without post-processing.

## Glossary

- **DynamoDBModelBase**: The base model class in `boto3_assist.dynamodb` from which all DynamoDB model classes inherit. Provides serialization, mapping, and merge capabilities.
- **to_dict**: A convenience method on DynamoDBModelBase that delegates to `to_dictionary`. Returns a dictionary representation of the model without index keys.
- **to_dictionary**: A method on DynamoDBModelBase that converts the model instance to a dictionary without DynamoDB index keys, suitable for general serialization.
- **Keys_Parameter**: An optional parameter accepting a list of strings representing top-level dictionary keys to retain in the output.
- **Filtered_Dictionary**: A dictionary containing only the top-level key-value pairs whose keys appear in the provided keys list.

## Requirements

### Requirement 1: Key Filtering on to_dictionary

**User Story:** As a developer, I want to pass a list of top-level keys to `to_dictionary`, so that the returned dictionary contains only the fields I need.

#### Acceptance Criteria

1. WHEN the Keys_Parameter is provided with a non-empty list, THE to_dictionary method SHALL return a Filtered_Dictionary containing only the top-level key-value pairs whose keys are present in the Keys_Parameter list.
2. WHEN the Keys_Parameter is provided and a specified key does not exist in the full dictionary, THE to_dictionary method SHALL silently omit that key from the Filtered_Dictionary.
3. WHEN the Keys_Parameter is None or not provided, THE to_dictionary method SHALL return the full dictionary, preserving current default behavior.
4. WHEN the Keys_Parameter is provided as an empty list, THE to_dictionary method SHALL return an empty dictionary.

### Requirement 2: Key Filtering on to_dict

**User Story:** As a developer, I want `to_dict` to support the same key filtering as `to_dictionary`, so that both convenience methods behave consistently.

#### Acceptance Criteria

1. THE to_dict method SHALL accept the same Keys_Parameter as to_dictionary.
2. WHEN the Keys_Parameter is provided, THE to_dict method SHALL delegate to to_dictionary with the Keys_Parameter and return the same Filtered_Dictionary.
3. WHEN the Keys_Parameter is None or not provided, THE to_dict method SHALL return the full dictionary, preserving current default behavior.

### Requirement 3: Filtering Applies After Serialization

**User Story:** As a developer, I want key filtering to happen after the full serialization pass, so that the filtering does not interfere with the serialization logic.

#### Acceptance Criteria

1. THE to_dictionary method SHALL perform the full serialization via DynamoDBSerializer.to_resource_dictionary before applying the key filter.
2. WHEN the Keys_Parameter is provided, THE to_dictionary method SHALL filter the serialized dictionary by retaining only top-level keys present in the Keys_Parameter list.

### Requirement 4: Round-Trip Consistency

**User Story:** As a developer, I want to verify that filtering keys and then mapping back produces a partial but consistent object, so that I can trust the filtered output.

#### Acceptance Criteria

1. FOR ALL valid DynamoDBModelBase instances and any subset of top-level keys, calling to_dictionary with the Keys_Parameter and then mapping the Filtered_Dictionary back onto a new instance of the same type SHALL produce an instance where each filtered key's attribute matches the original instance's attribute value.
