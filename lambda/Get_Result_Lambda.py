import json
import boto3
import os

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

TABLE_NAME = os.environ.get(
    "TABLE_NAME",
    "ServerlessImageMetadata"
)

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    try:
        params = event.get("queryStringParameters") or {}
        image_id = params.get("id")

        if not image_id:
            return response(400, {
                "error": "Missing id parameter"
            })

        result = table.get_item(
            Key={
                "image_id": image_id
            }
        )

        item = result.get("Item")

        if not item:
            return response(404, {
                "error": "Image not found"
            })

        # Generate temporary URL for thumbnail
        thumbnail_key = item.get("thumbnail_key")

        if thumbnail_key:
            thumbnail_url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": PROCESSED_BUCKET,
                    "Key": thumbnail_key
                },
                ExpiresIn=300
            )

            item["thumbnail_url"] = thumbnail_url

        return response(200, item)

    except Exception as e:
        print(f"Error: {str(e)}")

        return response(500, {
            "error": "Internal server error"
        })


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(body, default=str)
    }
