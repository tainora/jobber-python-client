"""Unit tests for jobber.photos module (S3 photo upload integration)."""

import subprocess
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import BotoCoreError, ClientError

from jobber.exceptions import JobberException
from jobber.photos import (
    attach_photos_to_visit,
    format_photo_urls_markdown,
    generate_presigned_upload_url,
    get_s3_credentials_from_doppler,
)


class TestGetS3CredentialsFromDoppler:
    """Test Doppler S3 credentials retrieval."""

    @patch("subprocess.run")
    def test_returns_credentials_on_success(self, mock_run: Mock) -> None:
        """get_s3_credentials_from_doppler() returns credentials dict."""
        # Mock subprocess.run to return credentials
        mock_run.side_effect = [
            Mock(stdout="AKIAIOSFODNN7EXAMPLE"),  # AWS_ACCESS_KEY_ID
            Mock(stdout="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),  # AWS_SECRET_ACCESS_KEY
            Mock(stdout="my-photo-bucket"),  # S3_BUCKET_NAME
        ]

        result = get_s3_credentials_from_doppler()

        assert result == {
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "bucket_name": "my-photo-bucket",
        }

    @patch("subprocess.run")
    def test_raises_exception_on_incomplete_credentials(self, mock_run: Mock) -> None:
        """Raises JobberException when any credential is empty."""
        # Mock subprocess.run to return empty secret key
        mock_run.side_effect = [
            Mock(stdout="AKIAIOSFODNN7EXAMPLE"),  # AWS_ACCESS_KEY_ID
            Mock(stdout=""),  # AWS_SECRET_ACCESS_KEY (empty)
            Mock(stdout="my-photo-bucket"),  # S3_BUCKET_NAME
        ]

        with pytest.raises(JobberException, match="S3 credentials incomplete"):
            get_s3_credentials_from_doppler()

    @patch("subprocess.run")
    def test_raises_exception_on_doppler_subprocess_failure(self, mock_run: Mock) -> None:
        """Raises JobberException when Doppler subprocess call fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["doppler", "secrets", "get"], stderr="Doppler error"
        )

        with pytest.raises(JobberException, match="Failed to fetch S3 credentials"):
            get_s3_credentials_from_doppler()


class TestGeneratePresignedUploadUrl:
    """Test S3 presigned URL generation."""

    @patch("jobber.photos.boto3.client")
    def test_generates_presigned_url_with_explicit_credentials(
        self, mock_boto3_client: Mock
    ) -> None:
        """generate_presigned_upload_url() creates presigned URL with provided credentials."""
        mock_s3_client = Mock()
        mock_s3_client.generate_presigned_url.return_value = (
            "https://my-bucket.s3.amazonaws.com/photos/roof.jpg?AWSAccessKeyId=..."
        )
        mock_boto3_client.return_value = mock_s3_client

        url = generate_presigned_upload_url(
            bucket="my-bucket",
            key="photos/roof.jpg",
            expires_in=3600,
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )

        # Verify boto3.client called with credentials
        mock_boto3_client.assert_called_once_with(
            "s3",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )

        # Verify generate_presigned_url called with correct params
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={"Bucket": "my-bucket", "Key": "photos/roof.jpg"},
            ExpiresIn=3600,
        )

        assert url == "https://my-bucket.s3.amazonaws.com/photos/roof.jpg?AWSAccessKeyId=..."

    @patch("jobber.photos.get_s3_credentials_from_doppler")
    @patch("jobber.photos.boto3.client")
    def test_fetches_credentials_from_doppler_when_not_provided(
        self, mock_boto3_client: Mock, mock_get_creds: Mock
    ) -> None:
        """Fetches credentials from Doppler when not explicitly provided."""
        # Mock Doppler credentials
        mock_get_creds.return_value = {
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "bucket_name": "my-photo-bucket",
        }

        mock_s3_client = Mock()
        mock_s3_client.generate_presigned_url.return_value = (
            "https://my-bucket.s3.amazonaws.com/photos/roof.jpg?AWSAccessKeyId=..."
        )
        mock_boto3_client.return_value = mock_s3_client

        url = generate_presigned_upload_url(bucket="my-bucket", key="photos/roof.jpg")

        # Verify Doppler credentials were fetched
        mock_get_creds.assert_called_once()

        # Verify boto3.client called with Doppler credentials
        mock_boto3_client.assert_called_once_with(
            "s3",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )

        assert url == "https://my-bucket.s3.amazonaws.com/photos/roof.jpg?AWSAccessKeyId=..."

    @patch("jobber.photos.boto3.client")
    def test_raises_exception_on_boto3_client_error(self, mock_boto3_client: Mock) -> None:
        """Raises JobberException when boto3 client creation fails."""
        mock_boto3_client.side_effect = ClientError(
            error_response={"Error": {"Code": "InvalidAccessKeyId", "Message": "Invalid key"}},
            operation_name="CreateClient",
        )

        with pytest.raises(JobberException, match="Failed to generate presigned URL"):
            generate_presigned_upload_url(
                bucket="my-bucket",
                key="photos/roof.jpg",
                aws_access_key_id="INVALID",
                aws_secret_access_key="INVALID",
            )

    @patch("jobber.photos.boto3.client")
    def test_raises_exception_on_presigned_url_generation_failure(
        self, mock_boto3_client: Mock
    ) -> None:
        """Raises JobberException when presigned URL generation fails."""
        mock_s3_client = Mock()
        mock_s3_client.generate_presigned_url.side_effect = BotoCoreError()
        mock_boto3_client.return_value = mock_s3_client

        with pytest.raises(JobberException, match="Failed to generate presigned URL"):
            generate_presigned_upload_url(
                bucket="my-bucket",
                key="photos/roof.jpg",
                aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            )


class TestAttachPhotosToVisit:
    """Test photo attachment to Jobber visits."""

    def test_creates_note_with_photo_links(self) -> None:
        """attach_photos_to_visit() creates note with markdown photo links."""
        mock_client = Mock()
        mock_client.execute_query.return_value = {
            "noteCreate": {
                "note": {
                    "id": "note-123",
                    "body": "## Photos\n\n[Photo 1: before.jpg](...)\n[Photo 2: after.jpg](...)",
                    "createdAt": "2025-11-22T10:00:00Z",
                }
            }
        }

        photo_urls = [
            "https://my-bucket.s3.amazonaws.com/photos/before.jpg",
            "https://my-bucket.s3.amazonaws.com/photos/after.jpg",
        ]

        result = attach_photos_to_visit(mock_client, visit_id="visit-456", photo_urls=photo_urls)

        # Verify mutation was called
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args

        # Verify mutation string contains noteCreate
        assert "noteCreate" in call_args[0][0]

        # Verify variables contain correct visit ID and photo content
        variables = call_args[0][1]
        assert variables["visitId"] == "visit-456"
        assert "Photo 1: before.jpg" in variables["content"]
        assert "Photo 2: after.jpg" in variables["content"]
        assert "https://my-bucket.s3.amazonaws.com/photos/before.jpg" in variables["content"]
        assert "https://my-bucket.s3.amazonaws.com/photos/after.jpg" in variables["content"]

        # Verify result returned correctly
        assert result["noteCreate"]["note"]["id"] == "note-123"

    def test_uses_custom_note_title(self) -> None:
        """attach_photos_to_visit() uses custom note title when provided."""
        mock_client = Mock()
        mock_client.execute_query.return_value = {"noteCreate": {"note": {"id": "note-123"}}}

        photo_urls = ["https://my-bucket.s3.amazonaws.com/photos/roof.jpg"]

        attach_photos_to_visit(
            mock_client,
            visit_id="visit-456",
            photo_urls=photo_urls,
            note_title="Roof Cleaning - Before/After",
        )

        # Verify custom title in note content
        call_args = mock_client.execute_query.call_args
        variables = call_args[0][1]
        assert "## Roof Cleaning - Before/After" in variables["content"]

    def test_raises_exception_on_mutation_failure(self) -> None:
        """Raises JobberException when GraphQL mutation fails."""
        mock_client = Mock()
        mock_client.execute_query.side_effect = Exception("GraphQL error")

        photo_urls = ["https://my-bucket.s3.amazonaws.com/photos/roof.jpg"]

        with pytest.raises(JobberException, match="Failed to attach photos to visit"):
            attach_photos_to_visit(mock_client, visit_id="visit-456", photo_urls=photo_urls)


class TestFormatPhotoUrlsMarkdown:
    """Test markdown formatting for photo URLs."""

    def test_formats_single_photo(self) -> None:
        """format_photo_urls_markdown() formats single photo as markdown."""
        urls = ["https://my-bucket.s3.amazonaws.com/photos/roof.jpg"]
        markdown = format_photo_urls_markdown(urls)

        expected = "## Photos\n\n[Photo 1: roof.jpg](https://my-bucket.s3.amazonaws.com/photos/roof.jpg)"
        assert markdown == expected

    def test_formats_multiple_photos(self) -> None:
        """format_photo_urls_markdown() formats multiple photos as numbered list."""
        urls = [
            "https://my-bucket.s3.amazonaws.com/photos/before.jpg",
            "https://my-bucket.s3.amazonaws.com/photos/after.jpg",
            "https://my-bucket.s3.amazonaws.com/photos/detail.jpg",
        ]
        markdown = format_photo_urls_markdown(urls)

        assert "## Photos" in markdown
        assert "[Photo 1: before.jpg](https://my-bucket.s3.amazonaws.com/photos/before.jpg)" in markdown
        assert "[Photo 2: after.jpg](https://my-bucket.s3.amazonaws.com/photos/after.jpg)" in markdown
        assert "[Photo 3: detail.jpg](https://my-bucket.s3.amazonaws.com/photos/detail.jpg)" in markdown

    def test_uses_custom_title(self) -> None:
        """format_photo_urls_markdown() uses custom title when provided."""
        urls = ["https://my-bucket.s3.amazonaws.com/photos/roof.jpg"]
        markdown = format_photo_urls_markdown(urls, title="Roof Inspection")

        assert "## Roof Inspection" in markdown
        assert "[Photo 1: roof.jpg]" in markdown

    def test_extracts_filename_from_url(self) -> None:
        """format_photo_urls_markdown() extracts filename from S3 URL."""
        urls = ["https://my-bucket.s3.amazonaws.com/path/to/complex/filename-123.jpg"]
        markdown = format_photo_urls_markdown(urls)

        # Should extract only the filename (last segment after /)
        assert "[Photo 1: filename-123.jpg]" in markdown

    def test_handles_empty_list(self) -> None:
        """format_photo_urls_markdown() handles empty photo list."""
        markdown = format_photo_urls_markdown([])

        assert markdown == "## Photos\n\n"
