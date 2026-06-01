import json
import os
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TOKENS_TABLE'])
BUCKET = os.environ['UPLOAD_BUCKET']
PRESIGN_EXPIRY = 300  # 5 minutes


def handler(event, context):
    params = event.get('queryStringParameters', {})
    token = params.get('token')
    filename = params.get('filename')

    if not token or not filename:
        return response(400, {'error': 'Missing token or filename'})

    # Validate token
    try:
        item = table.get_item(Key={'token': token}).get('Item')
    except ClientError:
        return response(500, {'error': 'Internal error'})

    if not item:
        return response(403, {'error': 'Invalid token'})

    # Generate short-lived presigned upload URL
    key = f"uploads/{token}/{filename}"
    url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': BUCKET,
            'Key': key,
            'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        },
        ExpiresIn=PRESIGN_EXPIRY
    )

    return response(200, {'uploadUrl': url})


def response(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
