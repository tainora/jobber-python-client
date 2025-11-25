"""
Photo upload integration for Jobber GraphQL API using S3-compatible storage.

Supports AWS S3 and Cloudflare R2 (S3-compatible) for mobile photo uploads.
Provides presigned URL generation and helpers to attach photo links to Jobber visits.

Example usage:
    from jobber.photos import generate_presigned_upload_url, attach_photos_to_visit

    # Generate presigned URL for mobile upload (works with S3 or R2)
    url = generate_presigned_upload_url("my-bucket", "photos/roof-123.jpg")

    # Upload photo from mobile app
    requests.put(url, data=photo_bytes, headers={"Content-Type": "image/jpeg"})

    # Attach photos to visit
    attach_photos_to_visit(client, visit_id="12345", photo_urls=[
        "https://my-bucket.s3.amazonaws.com/photos/before.jpg",
        "https://my-bucket.r2.cloudflarestorage.com/photos/after.jpg",
    ])
"""

import subprocess
from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]

from .exceptions import JobberException


def get_s3_credentials_from_doppler(
    project: str = "jobber", config: str = "prd"
) -> dict[str, str]:
    """
    Get S3-compatible storage credentials from Doppler secrets manager.

    Supports both AWS S3 and Cloudflare R2 (or any S3-compatible storage).

    Args:
        project: Doppler project name (default: "jobber")
        config: Doppler config name (default: "prd")

    Returns:
        Dictionary with:
        - 'aws_access_key_id': Access key ID
        - 'aws_secret_access_key': Secret access key
        - 'bucket_name': Bucket name
        - 'endpoint_url': S3 endpoint URL (empty string for AWS S3, URL for R2)

    Raises:
        JobberException: If Doppler secrets not found or invalid

    Example:
        >>> creds = get_s3_credentials_from_doppler("jobber", "prd")
        >>> print(creds['bucket_name'])
        jobber-photos-prd
    """
    base_cmd = ["doppler", "secrets", "get", "--plain", "--project", project, "--config", config]

    try:
        access_key = subprocess.run(
            base_cmd + ["CLOUD_STORAGE_ACCESS_KEY_ID"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        secret_key = subprocess.run(
            base_cmd + ["CLOUD_STORAGE_SECRET_ACCESS_KEY"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        bucket_name = subprocess.run(
            base_cmd + ["CLOUD_STORAGE_BUCKET_NAME"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        # Endpoint URL is optional (empty for AWS S3, required for R2)
        endpoint_result = subprocess.run(
            base_cmd + ["CLOUD_STORAGE_ENDPOINT_URL"],
            capture_output=True,
            text=True,
            check=False,  # Don't fail if missing (AWS S3 doesn't need it)
        )
        endpoint_url = endpoint_result.stdout.strip() if endpoint_result.returncode == 0 else ""

        if not all([access_key, secret_key, bucket_name]):
            raise JobberException(
                "Cloud storage credentials incomplete in Doppler",
                context={
                    "project": project,
                    "config": config,
                    "has_access_key": bool(access_key),
                    "has_secret_key": bool(secret_key),
                    "has_bucket_name": bool(bucket_name),
                },
            )

        return {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "bucket_name": bucket_name,
            "endpoint_url": endpoint_url,
        }

    except subprocess.CalledProcessError as e:
        raise JobberException(
            f"Failed to fetch cloud storage credentials from Doppler ({project}/{config})",
            context={"error": str(e), "stderr": e.stderr, "project": project, "config": config},
        ) from e


def generate_presigned_upload_url(
    bucket: str,
    key: str,
    expires_in: int = 3600,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    endpoint_url: str | None = None,
    project: str = "jobber",
    config: str = "prd",
) -> str:
    """
    Generate S3-compatible presigned URL for photo upload.

    Creates a presigned URL that allows mobile apps to upload photos directly
    to S3/R2 without exposing credentials. Works with AWS S3 and Cloudflare R2.

    Args:
        bucket: S3 bucket name
        key: Object key (path) in bucket (e.g., "photos/roof-123.jpg")
        expires_in: URL expiration time in seconds (default: 3600 = 1 hour)
        aws_access_key_id: Access key (optional, fetches from Doppler if None)
        aws_secret_access_key: Secret key (optional, fetches from Doppler if None)
        endpoint_url: S3 endpoint URL (optional, for R2/non-AWS; fetches from Doppler if None)
        project: Doppler project (default: "jobber")
        config: Doppler config (default: "prd")

    Returns:
        Presigned URL for PUT request

    Raises:
        JobberException: If client creation or URL generation fails

    Example:
        >>> # Cloudflare R2 (endpoint fetched from Doppler)
        >>> url = generate_presigned_upload_url("my-bucket", "photos/roof-123.jpg")
        >>> # Mobile app uploads: requests.put(url, data=photo_bytes)
        >>> # Photo accessible at: https://my-bucket.r2.cloudflarestorage.com/photos/roof-123.jpg

        >>> # AWS S3 (no endpoint needed)
        >>> url = generate_presigned_upload_url("my-bucket", "photos/roof-123.jpg")
        >>> # Photo accessible at: https://my-bucket.s3.amazonaws.com/photos/roof-123.jpg
    """
    # Fetch credentials from Doppler if not provided
    if not aws_access_key_id or not aws_secret_access_key:
        creds = get_s3_credentials_from_doppler(project, config)
        aws_access_key_id = creds["aws_access_key_id"]
        aws_secret_access_key = creds["aws_secret_access_key"]
        # Use endpoint from Doppler if not explicitly provided
        if endpoint_url is None:
            endpoint_url = creds["endpoint_url"] or None

    try:
        # Create S3 client (works for both S3 and R2)
        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        s3_client = boto3.client(**client_kwargs)

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

        return presigned_url  # type: ignore[no-any-return]

    except (ClientError, BotoCoreError) as e:
        raise JobberException(
            f"Failed to generate presigned URL for {bucket}/{key}",
            context={
                "error": str(e),
                "expires_in": expires_in,
                "endpoint_url": endpoint_url or "default (AWS S3)",
            },
        ) from e


def attach_photos_to_visit(
    client: Any,
    visit_id: str,
    photo_urls: list[str],
    note_title: str = "Photos",
) -> dict[str, Any]:
    """
    Attach photos to Jobber visit by creating note with photo links.

    Creates a note on the visit with markdown-formatted photo links. Photos
    must already be uploaded to S3 (use generate_presigned_upload_url first).

    Args:
        client: JobberClient instance
        visit_id: Jobber visit ID
        photo_urls: List of S3 photo URLs
        note_title: Note title (default: "Photos")

    Returns:
        GraphQL mutation response with created note

    Raises:
        JobberException: If note creation fails

    Example:
        >>> from jobber import JobberClient
        >>> client = JobberClient.from_doppler()
        >>> attach_photos_to_visit(
        ...     client,
        ...     visit_id="12345",
        ...     photo_urls=[
        ...         "https://my-bucket.s3.amazonaws.com/photos/before.jpg",
        ...         "https://my-bucket.s3.amazonaws.com/photos/after.jpg",
        ...     ],
        ... )
    """
    # Format photos as markdown links
    photo_links = []
    for i, url in enumerate(photo_urls, 1):
        # Extract filename from URL for link text
        filename = url.split("/")[-1]
        photo_links.append(f"[Photo {i}: {filename}]({url})")

    note_content = f"## {note_title}\n\n" + "\n".join(photo_links)

    # Create note mutation
    mutation = """
        mutation($visitId: ID!, $content: String!) {
            noteCreate(input: {
                subject: { id: $visitId }
                body: $content
            }) {
                note {
                    id
                    body
                    createdAt
                }
            }
        }
    """

    variables = {"visitId": visit_id, "content": note_content}

    try:
        result = client.execute_query(mutation, variables)
        return result  # type: ignore[no-any-return]
    except Exception as e:
        raise JobberException(
            f"Failed to attach photos to visit {visit_id}",
            context={
                "visit_id": visit_id,
                "photo_count": len(photo_urls),
                "error": str(e),
            },
        ) from e


def format_photo_urls_markdown(photo_urls: list[str], title: str = "Photos") -> str:
    """
    Format photo URLs as markdown for notes.

    Args:
        photo_urls: List of S3 photo URLs
        title: Markdown title (default: "Photos")

    Returns:
        Markdown-formatted string with photo links

    Example:
        >>> urls = ["https://bucket.s3.amazonaws.com/before.jpg", "https://bucket.s3.amazonaws.com/after.jpg"]
        >>> markdown = format_photo_urls_markdown(urls, "Roof Cleaning - Before/After")
        >>> print(markdown)
        ## Roof Cleaning - Before/After
        <BLANKLINE>
        [Photo 1: before.jpg](https://bucket.s3.amazonaws.com/before.jpg)
        [Photo 2: after.jpg](https://bucket.s3.amazonaws.com/after.jpg)
    """
    photo_links = []
    for i, url in enumerate(photo_urls, 1):
        filename = url.split("/")[-1]
        photo_links.append(f"[Photo {i}: {filename}]({url})")

    return f"## {title}\n\n" + "\n".join(photo_links)


__all__ = [
    "get_s3_credentials_from_doppler",
    "generate_presigned_upload_url",
    "attach_photos_to_visit",
    "format_photo_urls_markdown",
]
