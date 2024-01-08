import sys
sys.path.append("/mnt/efs/easyocr")

import easyocr
import json
import requests
import boto3

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def add_data(id,date,ocr_text):

    dynamodb = boto3.client('dynamodb')
    table_name = 'inha-notice-posts'
    
    resp = dynamodb.get_item(TableName=table_name,
    Key={
        'contentID': {"S":id},
        'date' : {"S":date}
    }
    )
    before_set = []
    if "articleImgsTextData" in resp:
        before_set = resp["articleImgsTextData"]
    
    before_set = set(before_set)
    
    ocr_text = before_set.union(ocr_text)
    
    
    response = dynamodb.update_item(
    TableName=table_name,
    Key={
        'contentID': {"S":id},
        'date' : {"S":date}
    },
    UpdateExpression='ADD articleImgsTextData :val1'
    ,
    ExpressionAttributeValues={
        ':val1': {"SS" : list(ocr_text)},
    },
    ReturnValues='UPDATED_NEW'
    )
    

def ocr(img):
    reader = easyocr.Reader(['ko','en'],model_storage_directory="/mnt/efs/img_to_text/model")
    result = reader.readtext(img,detail=0)
    
    return result

def lambda_handler(event, context=None):
    
    
    receiptHandle = event['Records'][0]['receiptHandle']
    records = event['Records'][0]['body']
    body = json.loads(records)
    
    sqs = boto3.client('sqs').delete_message(
    QueueUrl='https://sqs.us-east-2.amazonaws.com/629515838455/ImgTxtConverterTrigger',
    ReceiptHandle=receiptHandle
    )
    
    
    id = body['contentID']
    url = body['articleImg']
    date = body['date']
    
    
    
    logger.info("contentID: {}".format(id))
    logger.info("src: {}".format(url))
    logger.info("date: {}".format(date))
    
    imgPath = "/tmp/image"
    response = requests.get(url)
    
    with open(imgPath, 'wb') as file:
        file.write(response.content)
    
    ocr_text = ocr(imgPath)
    ocr_text = set([item.replace(" " , "") for item in ocr_text])
    

    add_data(id,date,ocr_text)
    
    
    
    logger.info("img to text: {}".format(ocr_text))
    

    
    return {
        "statusCode": 200,
        "body": list(ocr_text)
    }
