"""
Photo upload integration for Jobber GraphQL API using AWS S3.

Provides S3 presigned URL generation for mobile photo uploads and helpers
to attach photo links to Jobber visits via notes.

Example usage:
    from jobber.photos import generate_presigned_upload_url, attach_photos_to_visit

    # Generate presigned URL for mobile upload
    url = generate_presigned_upload_url("my-bucket", "photos/roof-123.jpg")

    # Upload photo to S3 (from mobile app)
    requests.put(url, data=photo_bytes, headers={"Content-Type": "image/jpeg"})

    # Attach photos to visit
    attach_photos_to_visit(client, visit_id="12345", photo_urls=[
        "https://my-bucket.s3.amazonaws.com/photos/before.jpg",
        "https://my-bucket.s3.amazonaws.com/photos/after.jpg",
    ])
"""

import subprocess
from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]

from .exceptions import JobberException


def get_s3_credentials_from_doppler() -> dict[str, str]:
    """
    Get S3 credentials from Doppler secrets manager.

    Returns:
        Dictionary with 'aws_access_key_id', 'aws_secret_access_key', 'bucket_name'

    Raises:
        JobberException: If Doppler secrets not found or invalid
    """
    try:
        access_key = subprocess.run(
            ["doppler", "secrets", "get", "AWS_ACCESS_KEY_ID", "--plain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        secret_key = subprocess.run(
            ["doppler", "secrets", "get", "AWS_SECRET_ACCESS_KEY", "--plain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        bucket_name = subprocess.run(
            ["doppler", "secrets", "get", "S3_BUCKET_NAME", "--plain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        if not all([access_key, secret_key, bucket_name]):
            raise JobberException(
                "S3 credentials incomplete in Doppler",
                context={
                    "has_access_key": bool(access_key),
                    "has_secret_key": bool(secret_key),
                    "has_bucket_name": bool(bucket_name),
                },
            )

        return {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "bucket_name": bucket_name,
        }

    except subprocess.CalledProcessError as e:
        raise JobberException(
            "Failed to fetch S3 credentials from Doppler",
            context={"error": str(e), "stderr": e.stderr},
        ) from e


def generate_presigned_upload_url(
    bucket: str,
    key: str,
    expires_in: int = 3600,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> str:
    """
    Generate S3 presigned URL for photo upload.

    Creates a presigned URL that allows mobile apps to upload photos directly
    to S3 without exposing AWS credentials. URL expires after specified time.

    Args:
        bucket: S3 bucket name
        key: Object key (path) in S3 bucket (e.g., "photos/roof-123.jpg")
        expires_in: URL expiration time in seconds (default: 3600 = 1 hour)
        aws_access_key_id: AWS access key (optional, fetches from Doppler if None)
        aws_secret_access_key: AWS secret key (optional, fetches from Doppler if None)

    Returns:
        Presigned URL for PUT request

    Raises:
        JobberException: If S3 client creation fails or presigned URL generation fails

    Example:
        >>> url = generate_presigned_upload_url("my-bucket", "photos/roof-123.jpg")
        >>> # Mobile app uploads: requests.put(url, data=photo_bytes)
        >>> # Photo accessible at: https://my-bucket.s3.amazonaws.com/photos/roof-123.jpg
    """
    # Fetch credentials from Doppler if not provided
    if not aws_access_key_id or not aws_secret_access_key:
        creds = get_s3_credentials_from_doppler()
        aws_access_key_id = creds["aws_access_key_id"]
        aws_secret_access_key = creds["aws_secret_access_key"]

    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

        return presigned_url  # type: ignore[no-any-return]

    except (ClientError, BotoCoreError) as e:
        raise JobberException(
            f"Failed to generate presigned URL for s3://{bucket}/{key}",
            context={"error": str(e), "expires_in": expires_in},
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
