#!/usr/bin/env python3
"""Generate a long random token and store it in DynamoDB."""
import argparse
import secrets
import boto3


def generate_token(table_name, customer_name, region='us-east-1'):
    token = secrets.token_urlsafe(48)  # 64-char URL-safe random string
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)
    table.put_item(Item={'token': token, 'customer': customer_name})
    return token


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a customer token')
    parser.add_argument('--table', required=True, help='DynamoDB table name')
    parser.add_argument('--customer', required=True, help='Customer/org name')
    parser.add_argument('--region', default='us-east-1')
    parser.add_argument('--base-url', default='http://localhost:8080/index.html',
                        help='Base URL for the customer page')
    args = parser.parse_args()

    token = generate_token(args.table, args.customer, args.region)
    url = f"{args.base_url}?token={token}"
    print(f"Token:  {token}")
    print(f"URL:    {url}")
