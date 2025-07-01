import json
import boto3
import uuid
from decimal import Decimal

comprehend = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SentimentAnalysisResults')

def lambda_handler(event, context):
    try:
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No request body provided.'})
            }

        body = json.loads(event['body'])
        text = body.get('text', '')
        
        if not text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No text provided for analysis.'})
            }

        comprehend_response = comprehend.detect_sentiment(
            Text=text,
            LanguageCode='en'
        )
        
        sentiment = comprehend_response['Sentiment']
        confidence_scores = comprehend_response['SentimentScore']
        
        confidence_scores_decimal = {k: Decimal(str(v)) for k, v in confidence_scores.items()}

        item_id = str(uuid.uuid4())

        item = {
            'id': item_id,
            'text': text,
            'sentiment': sentiment,
            'confidence_scores': confidence_scores_decimal
        }
        
        table.put_item(Item=item)
        
        response = {
            'id': item_id,
            'message': 'Sentiment analysis successful!',
            'text': text,
            'sentiment': sentiment,
            'confidence_scores': confidence_scores
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(response, default=str)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'An internal error occurred during sentiment analysis.',
                'message': str(e)
            })
        }
