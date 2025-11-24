#!/usr/bin/env python3
"""
Complete photo upload workflow for Jobber roof cleaning operations.

This example demonstrates the complete flow:
1. Generate S3 presigned URL for mobile upload
2. Upload photo to S3 (simulated with requests.put)
3. Attach photos to Jobber visit via note
4. Print jobberWebUri for visual verification

Prerequisites:
- S3 bucket configured with CORS
- AWS credentials in Doppler: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME
- Jobber OAuth tokens in Doppler
- boto3 installed: uv pip install boto3

S3 Bucket Setup:
1. Create S3 bucket: aws s3 mb s3://my-bucket
2. Configure CORS (allow PUT from mobile apps):
   {
     "CORSRules": [
       {
         "AllowedOrigins": ["*"],
         "AllowedMethods": ["PUT", "GET"],
         "AllowedHeaders": ["*"],
         "MaxAgeSeconds": 3000
       }
     ]
   }
3. Set bucket policy (public read for photos):
   {
     "Statement": [{
       "Effect": "Allow",
       "Principal": "*",
       "Action": "s3:GetObject",
       "Resource": "arn:aws:s3:::my-bucket/photos/*"
     }]
   }

Usage:
    python examples/photo_upload_workflow.py
"""

# /// script
# dependencies = [
#   "requests>=2.32.0",
#   "boto3>=1.35.0",
# ]
# ///

import time
from datetime import datetime

import requests

from jobber import JobberClient
from jobber.photos import (
    attach_photos_to_visit,
    generate_presigned_upload_url,
    get_s3_credentials_from_doppler,
)


def simulate_mobile_photo_upload(
    presigned_url: str, photo_data: bytes, content_type: str = "image/jpeg"
) -> bool:
    """
    Simulate mobile app uploading photo to S3 via presigned URL.

    Args:
        presigned_url: S3 presigned URL for PUT request
        photo_data: Photo bytes (actual photo from camera)
        content_type: MIME type (default: image/jpeg)

    Returns:
        True if upload succeeded
    """
    response = requests.put(presigned_url, data=photo_data, headers={"Content-Type": content_type})

    if response.status_code == 200:
        print("✅ Photo uploaded successfully to S3")
        return True
    else:
        print(f"❌ Photo upload failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def main():
    print("=" * 70)
    print("📸 Jobber Photo Upload Workflow")
    print("=" * 70)
    print()

    # Step 1: Get S3 credentials from Doppler
    print("Step 1: Fetching S3 credentials from Doppler...")
    try:
        creds = get_s3_credentials_from_doppler()
        bucket_name = creds["bucket_name"]
        print(f"   ✅ S3 bucket: {bucket_name}")
    except Exception as e:
        print(f"   ❌ Failed to fetch credentials: {e}")
        print()
        print("Make sure these secrets are set in Doppler:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - S3_BUCKET_NAME")
        return

    print()

    # Step 2: Generate presigned URLs for before/after photos
    print("Step 2: Generating presigned URLs for photo uploads...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    before_key = f"photos/roof_{timestamp}_before.jpg"
    after_key = f"photos/roof_{timestamp}_after.jpg"

    try:
        before_url = generate_presigned_upload_url(bucket_name, before_key)
        after_url = generate_presigned_upload_url(bucket_name, after_key)

        print(f"   ✅ Before photo URL: {before_url[:80]}...")
        print(f"   ✅ After photo URL: {after_url[:80]}...")
        print("   ⏱️  URLs expire in 1 hour")
    except Exception as e:
        print(f"   ❌ Failed to generate presigned URLs: {e}")
        return

    print()

    # Step 3: Simulate mobile upload (in real app, this happens from camera)
    print("Step 3: Simulating mobile photo uploads...")

    # Create dummy photo data (in real app, this comes from device camera)
    dummy_before = b"JPEG_PHOTO_DATA_BEFORE" * 100  # Simulate JPEG bytes
    dummy_after = b"JPEG_PHOTO_DATA_AFTER" * 100

    # Upload photos to S3
    if not simulate_mobile_photo_upload(before_url, dummy_before):
        return
    time.sleep(1)  # Simulate realistic upload timing

    if not simulate_mobile_photo_upload(after_url, dummy_after):
        return

    print()

    # Step 4: Construct public S3 URLs
    print("Step 4: Constructing public S3 URLs for photos...")

    before_public_url = f"https://{bucket_name}.s3.amazonaws.com/{before_key}"
    after_public_url = f"https://{bucket_name}.s3.amazonaws.com/{after_key}"

    print(f"   📷 Before: {before_public_url}")
    print(f"   📷 After: {after_public_url}")

    print()

    # Step 5: Get or create a Jobber visit
    print("Step 5: Finding a Jobber visit to attach photos to...")

    try:
        client = JobberClient.from_doppler()

        # Query recent visits
        query = """
            query {
                visits(first: 1) {
                    nodes {
                        id
                        title
                        jobberWebUri
                        client {
                            name
                        }
                    }
                }
            }
        """

        result = client.execute_query(query)
        visits = result["data"]["visits"]["nodes"]

        if not visits:
            print("   ⚠️  No visits found in Jobber account")
            print("   Create a visit first, then re-run this example")
            return

        visit = visits[0]
        visit_id = visit["id"]
        visit_title = visit["title"]
        client_name = visit["client"]["name"]
        visit_web_uri = visit["jobberWebUri"]

        print(f"   ✅ Found visit: {visit_title}")
        print(f"      Client: {client_name}")
        print(f"      Visit ID: {visit_id}")

    except Exception as e:
        print(f"   ❌ Failed to query Jobber visits: {e}")
        return

    print()

    # Step 6: Attach photos to visit via note
    print("Step 6: Attaching photos to visit...")

    try:
        attach_photos_to_visit(
            client,
            visit_id=visit_id,
            photo_urls=[before_public_url, after_public_url],
            note_title="Roof Cleaning - Before/After Photos",
        )

        print("   ✅ Photos attached to visit via note")
        print("   📝 Note created with 2 photo links")

    except Exception as e:
        print(f"   ❌ Failed to attach photos: {e}")
        return

    print()

    # Step 7: Visual verification
    print("Step 7: Visual verification")
    print(f"   🌐 View visit in Jobber: {visit_web_uri}")
    print("   👉 Click link to see photos in note")

    print()
    print("=" * 70)
    print("✅ Complete workflow executed successfully!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Generated 2 presigned URLs")
    print("  - Uploaded 2 photos to S3")
    print(f"  - Attached photos to visit {visit_id}")
    print(f"  - Photos visible in Jobber at: {visit_web_uri}")
    print()
    print("Next steps:")
    print("  1. Click the jobberWebUri link above")
    print("  2. View the visit in Jobber")
    print("  3. Open the 'Roof Cleaning - Before/After Photos' note")
    print("  4. Click photo links to view images")


if __name__ == "__main__":
    main()
