import json
import os
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TOKENS_TABLE'])
BUCKET = os.environ['TEMPLATE_BUCKET']
TEMPLATE_KEY = os.environ['TEMPLATE_KEY']
PRESIGN_EXPIRY = 300  # 5 minutes


def handler(event, context):
    token = event.get('queryStringParameters', {}).get('token')
    if not token:
        return response(400, {'error': 'Missing token'})

    # Validate token
    try:
        item = table.get_item(Key={'token': token}).get('Item')
    except ClientError:
        return response(500, {'error': 'Internal error'})

    if not item:
        return response(403, {'error': 'Invalid token'})

    # Generate short-lived presigned download URL
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET, 'Key': TEMPLATE_KEY},
        ExpiresIn=PRESIGN_EXPIRY
    )

    return response(200, {'downloadUrl': url})


def response(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
