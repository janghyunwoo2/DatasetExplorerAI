# AWS Bedrock 인증
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def get_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION")
    )