import boto3
import json
import os
import uuid
import urllib.parse

s3 = boto3.client("s3")

UPLOAD_BUCKET = os.environ["UPLOAD_BUCKET"]


def lambda_handler(event, context):

    print("Generating presigned upload URL")

    body = event.get("body", "{}")

    if isinstance(body, str):
        body = json.loads(body)

    filename = body.get("filename")
    content_type = body.get("contentType")

    if not filename or not content_type:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "filename and contentType are required"
            })
        }

    # Generate one unique ID
    image_id = str(uuid.uuid4())

    # Keep original filename safe
    safe_filename = urllib.parse.quote(
        os.path.basename(filename)
    )

    # Use the SAME image_id in the S3 key
    object_key = f"uploads/{image_id}-{safe_filename}"

    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": UPLOAD_BUCKET,
            "Key": object_key,
            "ContentType": content_type
        },
        ExpiresIn=300
    )

    print(f"Image ID: {image_id}")
    print(f"Generated upload key: {object_key}")

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "uploadUrl": upload_url,
            "key": object_key,
            "image_id": image_id
        })
    }
