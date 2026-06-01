import json
import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TOKENS_TABLE'])


def handler(event, context):
    token = event.get('queryStringParameters', {}).get('token')
    if not token:
        return response(400, {'error': 'Missing token'})

    try:
        item = table.get_item(Key={'token': token}).get('Item')
    except ClientError:
        return response(500, {'error': 'Internal error'})

    if not item:
        return response(403, {'error': 'Invalid or expired token'})

    return response(200, {'valid': True, 'customer': item.get('customer', '')})


def response(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
