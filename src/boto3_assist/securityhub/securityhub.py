"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
from typing import Optional, Literal

from aws_lambda_powertools import Logger

from boto3_assist.securityhub.securityhub_connection import SecurityHubConnection

logger = Logger("security-hub-service")


class SecurityHub(SecurityHubConnection):
    """Security Hub Service"""

    def update_findings_status(
        self,
        region_name: str,
        workflow_status: Literal["NEW", "NOTIFIED", "RESOLVED", "SUPPRESSED"],
        note_text: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        """
        Updates the workflow status for all findings in the specified region.

        :param region_name: AWS region where Security Hub findings are located.
        :param workflow_status: The new workflow status to apply (e.g., NEW, NOTIFIED, SUPPRESSED, RESOLVED).
        """
        # Initialize Security Hub client
        client = self.client

        findings_to_update = []
        next_token = None

        logger.info(f"Fetching findings in region: {region_name}...")

        try:
            # Paginate through findings
            while True:
                response = client.get_findings(
                    MaxResults=100,
                    Filters={
                        "Region": [
                            {"Value": region_name, "Comparison": "EQUALS"},
                        ]
                    },
                    NextToken=next_token if next_token else "",
                )

                for finding in response.get("Findings", []):
                    current_status = finding.get("Workflow", {}).get("Status")
                    if (
                        current_status
                        and str(current_status).lower() != str(workflow_status).lower()
                    ):
                        findings_to_update.append(
                            {
                                "Id": finding["Id"],
                                "ProductArn": finding["ProductArn"],
                            }
                        )
                    else:
                        logger.debug(
                            f"Skipping: {finding['Id']} with a status of {current_status}"
                        )

                next_token = response.get("NextToken")
                if not next_token:
                    break

            print(f"Found {len(findings_to_update)} findings to update.")

            note_text = note_text or "Automated Update"
            updated_by = updated_by or "System"
            # Update workflow status in batches of 100
            for i in range(0, len(findings_to_update), 100):
                batch = findings_to_update[i : i + 100]
                response = client.batch_update_findings(
                    FindingIdentifiers=batch,
                    Workflow={"Status": str(workflow_status).upper()},
                    Note={"Text": note_text, "UpdatedBy": updated_by},
                )
                logger.debug(
                    f"Updated findings {i + 1} to {i + len(batch)} to status: {workflow_status}"
                )
                print(response)

            logger.info("All findings updated successfully!")

        except Exception as e:
            logger.exception(f"An error occurred: {str(e)}")
            raise


def main():
    status = "RESOLVED"  # Change to NEW, NOTIFIED, SUPPRESSED, or RESOLVED
    note_text = "This region is now disabled."
    # these are my linked regions and the only ones I care about
    # if have SCP's in place for the other regions
    regions_to_skip = ["us-east-1", "us-west-2", "eu-west-2"]

    aws_profile = os.getenv("SECURITY_HUB_PROFILE")

    aws_regions = {
        "af-south-1": "Africa (Cape Town)",
        "ap-east-1": "Asia Pacific (Hong Kong)",
        "ap-northeast-1": "Asia Pacific (Tokyo)",
        "ap-northeast-2": "Asia Pacific (Seoul)",
        "ap-northeast-3": "Asia Pacific (Osaka)",
        "ap-south-1": "Asia Pacific (Mumbai)",
        "ap-south-2": "Asia Pacific (Hyderabad)",
        "ap-southeast-1": "Asia Pacific (Singapore)",
        "ap-southeast-2": "Asia Pacific (Sydney)",
        "ap-southeast-3": "Asia Pacific (Jakarta)",
        "ap-southeast-4": "Asia Pacific (Melbourne)",
        "ap-southeast-5": "Asia Pacific (Auckland)",
        "ca-central-1": "Canada (Central)",
        "ca-west-1": "Canada (West)",
        "eu-central-1": "Europe (Frankfurt)",
        "eu-central-2": "Europe (Zurich)",
        "eu-north-1": "Europe (Stockholm)",
        "eu-south-1": "Europe (Milan)",
        "eu-south-2": "Europe (Spain)",
        "eu-west-1": "Europe (Ireland)",
        "eu-west-2": "Europe (London)",
        "eu-west-3": "Europe (Paris)",
        "il-central-1": "Israel (Tel Aviv)",
        "me-central-1": "Middle East (UAE)",
        "sa-east-1": "South America (São Paulo)",
        "us-east-1": "US East (N. Virginia)",
        "us-east-2": "US East (Ohio)",
        "us-west-1": "US West (N. California)",
        "us-west-2": "US West (Oregon)",
    }

    sh: SecurityHub = SecurityHub(aws_profile=aws_profile)
    for region in aws_regions:
        print(region)
        if region not in regions_to_skip:
            sh.update_findings_status(region, status, note_text=note_text)
        else:
            print(f"Skipping region: {region}")


if __name__ == "__main__":
    main()
