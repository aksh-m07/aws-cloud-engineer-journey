import json
import boto3

# Created once per container (cold start) and reused on warm invocations.
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Properties')


def lambda_handler(event, context):
    # API Gateway fills pathParameters from the {id} in GET /properties/{id}
    listing_id = event['pathParameters']['id']

    # DynamoDB GetItem: look up one row by its partition key
    resp = table.get_item(Key={'L_ListingID': listing_id})

    # default=str because DynamoDB returns numbers as Decimal, which json can't serialize
    return {
        'statusCode': 200,
        'body': json.dumps(resp.get('Item', {}), default=str)
    }
