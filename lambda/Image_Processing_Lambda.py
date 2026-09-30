import boto3
from PIL import Image
from io import BytesIO
import os
from datetime import datetime, timezone
import urllib.parse

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
TABLE_NAME = os.environ["TABLE_NAME"]

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):

    print("Image processing started")

    record = event["Records"][0]

    source_bucket = record["s3"]["bucket"]["name"]

    source_key = urllib.parse.unquote_plus(
        record["s3"]["object"]["key"]
    )

    print(f"Source bucket: {source_bucket}")
    print(f"Source key: {source_key}")

    # Extract image_id from:
    # uploads/<image_id>-<filename>
    object_name = os.path.basename(source_key)

    image_id = "-".join(object_name.split("-")[:5])

    print(f"Image ID: {image_id}")

    # Download original image
    response = s3.get_object(
        Bucket=source_bucket,
        Key=source_key
    )

    image_data = response["Body"].read()

    print(
        f"Downloaded image size: "
        f"{len(image_data)} bytes"
    )

    # Open image with Pillow
    image = Image.open(
        BytesIO(image_data)
    )

    original_width, original_height = image.size

    print(
        f"Original image size: "
        f"{original_width}x{original_height}"
    )

    # Convert transparency to RGB
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")

    # Create thumbnail
    image.thumbnail((300, 300))

    thumbnail_buffer = BytesIO()

    image.save(
        thumbnail_buffer,
        format="JPEG",
        quality=85
    )

    thumbnail_buffer.seek(0)

    # Thumbnail filename
    filename = os.path.basename(source_key)

    name_without_extension = os.path.splitext(
        filename
    )[0]

    thumbnail_key = (
        f"thumbnails/"
        f"{name_without_extension}-thumbnail.jpg"
    )

    # Upload thumbnail
    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=thumbnail_key,
        Body=thumbnail_buffer,
        ContentType="image/jpeg"
    )

    print(
        f"Thumbnail uploaded: "
        f"{thumbnail_key}"
    )

    # Metadata
    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    metadata = {
        "image_id": image_id,
        "filename": filename,
        "size": len(image_data),
        "timestamp": timestamp,
        "thumbnail_key": thumbnail_key,
        "original_width": original_width,
        "original_height": original_height
    }

    # Save metadata
    table.put_item(
        Item=metadata
    )

    print(
        f"Metadata saved to DynamoDB: "
        f"{image_id}"
    )

    return {
        "statusCode": 200,
        "body": "Image processed successfully"
    }
