import json

import boto3


class PracticeTimeWindowClient:
    def __init__(self, function_name, region_name=None):
        self._client = boto3.client("lambda", **({"region_name": region_name} if region_name else {}))
        self._function_name = function_name

    def put(self, practice_phone, body):
        event = {
            "resource": "/config/practice-time-window/{practice_phone}",
            "path": f"/config/practice-time-window/{practice_phone}",
            "httpMethod": "PUT",
            "headers": {"Content-Type": "application/json"},
            "queryStringParameters": None,
            "pathParameters": {"practice_phone": practice_phone},
            "stageVariables": None,
            "requestContext": {
                "resourcePath": "/config/practice-time-window/{practice_phone}",
                "httpMethod": "PUT",
                "path": f"/config/practice-time-window/{practice_phone}",
            },
            "body": json.dumps(body),
            "isBase64Encoded": False,
        }

        response = self._client.invoke(
            FunctionName=self._function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event),
        )
        return json.loads(response["Payload"].read())

    def put_batch(self, entries):
        """Send multiple entries. entries: dict of {phone: body} or list of (phone, body)."""
        results = []
        items = entries.items() if isinstance(entries, dict) else entries
        for phone, body in items:
            result = self.put(phone, body)
            results.append({"practice_phone": phone, "statusCode": result.get("statusCode"), "response": result})
        return results
