import boto3
from botocore.exceptions import ClientError
from .ecr_connection import ECRConnection


class ECR(ECRConnection):
    pass

    def retag_image(self, repository_name: str, source_tag: str, target_tag: str):
        """
        ReTag an ECR Image without the overhead of pulling it down, tagging and pushing.
        Simply retags by getting the manifest, and pushing up changes.
        Args:
            repository_name (str):

        """
        ecr = self.client

        try:
            # 1) Get the manifest for the source tag
            resp = ecr.batch_get_image(
                repositoryName=repository_name,
                imageIds=[{"imageTag": source_tag}],
                # optional, but helps ensure you get the right manifest type:
                acceptedMediaTypes=[
                    "application/vnd.docker.distribution.manifest.v2+json",
                    "application/vnd.oci.image.manifest.v1+json",
                ],
            )
            images = resp.get("images", [])
            if not images:
                raise RuntimeError(f"No image found with tag {source_tag!r}")

            manifest = images[0]["imageManifest"]

            # 2) Push the same manifest under the new tag
            put_resp = ecr.put_image(
                repositoryName=repository_name,
                imageManifest=manifest,
                imageTag=target_tag,
            )

            failures = put_resp.get("failures")

            if failures and len(failures) > 0:
                raise RuntimeError(
                    f"Failed to tag {repository_name}:{target_tag} - {failures}"
                )

            print(f"Successfully tagged {repository_name}:{target_tag}")
            return put_resp

        except ClientError as e:
            print(
                f"ECR error: {e.response.get('Error', {}).get('Code', 'NA')} "
                f"- {e.response.get('Error', {}).get('Message', 'NA')}"
            )
            raise


if __name__ == "__main__":
    # Example: retag version 1.16.54 → dev
    ecr: ECR = ECR(aws_profile="geek-cafe", aws_region="us-east-1")
    ecr.retag_image("my-repo", "1.16.54", "dev")
