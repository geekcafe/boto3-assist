# Partial Updates With Model

## Overview

We have a nice ORM pattern for our models `DynamoDBModelBase` and dynamodb interactions `class DynamoDB(DynamoDBConnection):` but we lack the ability to use the models and do selective field updates.

It would nice that if we want to partially populate a model and in the save or dedicated save_partial (or some better name), we can do a selective model mapping for the update expressions.



## Sample Model in our Boto3-Assist

```python
"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from typing import Optional

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class User(DynamoDBModelBase):
    """User Model"""

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
    ):
        super().__init__(self)
        self.id: Optional[str] = id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.age: Optional[int] = None
        self.email: Optional[str] = None
        # known reserved words
        self.status: Optional[str] = None

        self.__setup_indexes()

    def __setup_indexes(self):
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.partition_key.attribute_name = "pk"
        # allows for a wild card search on all "sites"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        self.indexes.add_primary(primary)

        gsi0: DynamoDBIndex = DynamoDBIndex(index_name="gsi1")
        gsi0.partition_key.attribute_name = "gsi1_pk"
        gsi0.partition_key.value = lambda: DynamoDBKey.build_key(("users", None))
        gsi0.sort_key.attribute_name = "gsi1_sk"
        gsi0.sort_key.value = lambda: DynamoDBKey.build_key(("email", self.email))
        self.indexes.add_secondary(gsi0)

        gsi1: DynamoDBIndex = DynamoDBIndex(index_name="gsi2")
        gsi1.partition_key.attribute_name = "gsi2_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(("users", None))
        gsi1.sort_key.attribute_name = "gsi2_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(
            ("lastname", self.last_name), ("firstname", self.first_name)
        )
        self.indexes.add_secondary(gsi1)

        gsi0: DynamoDBIndex = DynamoDBIndex(index_name="gsi3")
        gsi0.partition_key.attribute_name = "gsi3_pk"
        gsi0.partition_key.value = lambda: DynamoDBKey.build_key(("users", None))
        gsi0.sort_key.attribute_name = "gsi3_sk"
        gsi0.sort_key.value = lambda: DynamoDBKey.build_key(
            ("firstname", self.first_name), ("lastname", self.last_name)
        )
        self.indexes.add_secondary(gsi0)



```


## Sample of a selective update pattern in DynamoDB

```python
    def update_phase_status(
        self,
        execution_id: str,
        phase: str,
        status: str,
        version: Optional[str] = None,
        started_utc: Optional[str] = None,
        completed_utc: Optional[str] = None,
        duration_ms: Optional[int] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult:
        """
        Update a phase's status in the summary.

        Writes PhaseRecord via conditional UpdateItem (status_ordinal guard)
        and atomically updates RootSummaryRecord counters.

        Args:
            execution_id: Root execution ID
            phase: Phase name (e.g., "data_cleaning")
            status: New status
            version: Service version that ran this phase
            started_utc: When the phase started
            completed_utc: When the phase completed
            duration_ms: Phase duration
            error: Error info if the phase failed
        """
        try:
            now = datetime.now(UTC).isoformat()
            new_ordinal = STATUS_ORDINAL.get(status, 0)
            pk_value = f"execution#{execution_id}"

            logger.info(
                {
                    "summary_trace": True,
                    "action": "update_phase_status",
                    "execution_id": execution_id,
                    "phase": phase,
                    "status": status,
                    "result": "entry",
                }
            )

            # --- 1. Conditional UpdateItem on PhaseRecord ---
            # We need to find the phase's order to construct the sk.
            # Query for the phase records to find the matching one.
            phase_sk_prefix = "phase#"
            phase_items_resp = self.dynamodb.query(
                key=Key("pk").eq(pk_value) & Key("sk").begins_with(phase_sk_prefix),
                table_name=self.table_name,
                ascending=True,
            )
            phase_items = phase_items_resp.get("Items", [])

            target_phase = None
            for pi in phase_items:
                if pi.get("phase_name") == phase:
                    target_phase = pi
                    break

            if target_phase is None:
                existing_phases = [pi.get("phase_name") for pi in phase_items]
                logger.warning(
                    f"Phase '{phase}' not found for execution {execution_id}"
                )
                logger.info(
                    {
                        "summary_trace": True,
                        "action": "update_phase_status",
                        "execution_id": execution_id,
                        "phase": phase,
                        "status": status,
                        "result": "skipped_no_phase",
                        "existing_phases": existing_phases,
                    }
                )
                return ServiceResult.success_result(data=None)

            phase_sk = target_phase.get("sk")
            phase_key = {"pk": pk_value, "sk": phase_sk}

            # Build UpdateItem expression for phase
            update_parts = [
                "#s = :status",
                "status_ordinal = :ord",
                "updated_utc = :now",
            ]
            expr_values: Dict[str, Any] = {
                ":status": status,
                ":ord": new_ordinal,
                ":now": now,
            }
            expr_names: Dict[str, str] = {"#s": "status"}

            if version:
                update_parts.append("version = :ver")
                expr_values[":ver"] = version
            if started_utc:
                update_parts.append("started_utc = :started")
                expr_values[":started"] = started_utc
            if completed_utc:
                update_parts.append("completed_utc = :completed")
                expr_values[":completed"] = completed_utc
            if duration_ms is not None:
                update_parts.append("duration_ms = :dur")
                expr_values[":dur"] = duration_ms
            elif completed_utc and target_phase.get("started_utc"):
                calc_dur = self._calc_duration_ms(
                    target_phase["started_utc"], completed_utc
                )
                if calc_dur is not None:
                    update_parts.append("duration_ms = :dur")
                    expr_values[":dur"] = calc_dur

            update_expr = "SET " + ", ".join(update_parts)

            # Condition: allow write only if item doesn't exist or new ordinal is higher
            condition = "attribute_not_exists(sk) OR status_ordinal < :ord"

            try:
                self.dynamodb.update_item(
                    table_name=self.table_name,
                    key=phase_key,
                    update_expression=update_expr,
                    expression_attribute_values=expr_values,
                    expression_attribute_names=expr_names,
                    condition_expression=condition,
                )
            except (RuntimeError, ClientError) as ce:
                # ConditionalCheckFailedException → stale write, no-op
                error_str = str(ce)
                if (
                    "ConditionalCheckFailed" in error_str
                    or "Conditional check failed" in error_str
                ):
                    logger.warning(
                        f"Stale phase update for {phase} in {execution_id}: "
                        f"attempted {status} (ordinal {new_ordinal}), "
                        f"a more recent status already exists"
                    )
                    logger.info(
                        {
                            "summary_trace": True,
                            "action": "update_phase_status",
                            "execution_id": execution_id,
                            "phase": phase,
                            "status": status,
                            "result": "stale_write",
                            "attempted_ordinal": new_ordinal,
                        }
                    )
                    return ServiceResult.success_result(data=None)
                raise

            # --- 2. Atomic UpdateItem on RootSummaryRecord ---
            root_key = {"pk": pk_value, "sk": "summary"}
            root_update_parts = ["#s = :status", "updated_utc = :now"]
            root_expr_values: Dict[str, Any] = {":now": now}
            root_expr_names: Dict[str, str] = {"#s": "status"}

            if status == "running":
                root_expr_values[":status"] = "running"
                root_update_parts.append("current_phase = :phase")
                root_expr_values[":phase"] = phase
                # Clear any transient status message
                root_update_parts.append("status_message = :null_msg")
                root_expr_values[":null_msg"] = None
                # Set started_utc on root if this is the first phase to start
                if started_utc:
                    root_update_parts.append(
                        "started_utc = if_not_exists(started_utc, :started)"
                    )
                    root_expr_values[":started"] = started_utc
            else:
                root_expr_values[":status"] = (
                    status if status == "failed" else "running"
                )

            # Increment completed_phases for terminal statuses
            is_completed = status in ("succeeded", "completed")
            if is_completed:
                root_update_parts.append("completed_phases = completed_phases + :one")
                root_expr_values[":one"] = 1

            root_update_expr = "SET " + ", ".join(root_update_parts)

            try:
                self.dynamodb.update_item(
                    table_name=self.table_name,
                    key=root_key,
                    update_expression=root_update_expr,
                    expression_attribute_values=root_expr_values,
                    expression_attribute_names=root_expr_names,
                )
            except Exception as root_err:
                logger.exception(f"Error updating root for phase {phase}: {root_err}")

            # Update progress_percent after incrementing completed_phases
            if is_completed:
                try:
                    self._update_root_progress(pk_value)
                except Exception as prog_err:
                    logger.warning(f"Error updating progress_percent: {prog_err}")

            # --- 3. If phase failed, write an ErrorRecord ---
            if status == "failed" and error:
                try:
                    self._write_error_record(execution_id, error, phase=phase)
                except Exception as err_err:
                    logger.warning(
                        f"Error writing error record for phase {phase}: {err_err}"
                    )

            logger.info(
                {
                    "summary_trace": True,
                    "action": "update_phase_status",
                    "execution_id": execution_id,
                    "phase": phase,
                    "status": status,
                    "result": "success",
                }
            )

            return ServiceResult.success_result(data=None)

        except Exception as e:
            logger.exception(f"Error updating phase status: {e}")
            return ServiceResult.error_result(
                message=str(e), error_code="INTERNAL_ERROR"
            )

```
