"""Unit tests for case transformation utilities."""

import json
import os
from pathlib import Path

import pytest

from boto3_assist.utilities.string_utility import StringUtility


class TestCaseTransformation:
    """Tests for snake_case to camelCase conversion."""

    @pytest.fixture
    def files_dir(self) -> Path:
        """Return the path to the files subdirectory."""
        return Path(__file__).parent / "files"

    @pytest.fixture
    def output_dir(self) -> Path:
        """Return the path to the .output directory, creating it if needed."""
        output_path = Path(__file__).parent / ".output"
        output_path.mkdir(exist_ok=True)
        return output_path

    def convert_keys_to_camel_case(self, obj):
        """Recursively convert all dictionary keys from snake_case to camelCase."""
        if isinstance(obj, dict):
            return {
                StringUtility.snake_to_camel(key): self.convert_keys_to_camel_case(
                    value
                )
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [self.convert_keys_to_camel_case(item) for item in obj]
        else:
            return obj

    def test_snake_to_camel_basic(self):
        """Test basic snake_case to camelCase conversion."""
        assert StringUtility.snake_to_camel("hello_world") == "helloWorld"
        assert StringUtility.snake_to_camel("created_by_id") == "createdById"
        assert StringUtility.snake_to_camel("tenant_id") == "tenantId"
        assert StringUtility.snake_to_camel("single") == "single"

    def test_convert_files_to_camel_case(self, files_dir: Path, output_dir: Path):
        """
        Loop through all JSON files in the files subdirectory,
        convert keys from snake_case to camelCase, and write output
        to the .output directory for visual inspection.
        """
        json_files = list(files_dir.glob("*.json"))
        assert len(json_files) > 0, "No JSON files found in files directory"

        for json_file in json_files:
            # Read the input file
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert all keys from snake_case to camelCase
            converted_data = self.convert_keys_to_camel_case(data)

            # Write to output directory with same filename
            output_file = output_dir / json_file.name
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(converted_data, f, indent=4)

            # Verify the output file was created
            assert output_file.exists(), f"Output file {output_file} was not created"

            # Verify some key conversions occurred
            if isinstance(converted_data, list) and len(converted_data) > 0:
                first_item = converted_data[0]
                # Check that snake_case keys were converted
                assert (
                    "createdById" in first_item
                ), "Expected 'createdById' key after conversion"
                assert (
                    "tenantId" in first_item
                ), "Expected 'tenantId' key after conversion"
                assert (
                    "created_by_id" not in first_item
                ), "Key 'created_by_id' should have been converted"

            print(f"Converted {json_file.name} -> {output_file}")

    def test_nested_conversion(self, files_dir: Path, output_dir: Path):
        """Test that nested dictionaries are also converted."""
        json_files = list(files_dir.glob("*.json"))

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            converted_data = self.convert_keys_to_camel_case(data)

            # Check nested metadata conversion
            if isinstance(converted_data, list):
                for item in converted_data:
                    if "metadata" in item and isinstance(item["metadata"], dict):
                        metadata = item["metadata"]
                        # Verify nested keys are converted
                        if "converter" in metadata:
                            converter = metadata["converter"]
                            # Keys inside nested dicts should also be camelCase
                            assert "version" in converter or "timestamp" in converter
                        if "columnNames" in metadata:
                            # This was column_names in original
                            assert isinstance(metadata["columnNames"], list)

    def test_all_files_processed(self, files_dir: Path, output_dir: Path):
        """Verify all files in the files directory are processed."""
        json_files = list(files_dir.glob("*.json"))

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            converted_data = self.convert_keys_to_camel_case(data)
            output_file = output_dir / json_file.name

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(converted_data, f, indent=4)

        # Verify output count matches input count
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) >= len(json_files), "Not all files were converted"
