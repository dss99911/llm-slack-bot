from typing import Optional
import boto3

from langchain_aws import ChatBedrock

from util.aws.base import aws_region_name


def get_bedrock_client(runtime: Optional[bool] = True):
    """
    runtime :
        Optional choice of getting different client to perform operations with the Amazon Bedrock service.
    """
    if runtime:
        service_name='bedrock-runtime'
    else:
        service_name='bedrock'
    bedrock_client = boto3.client(service_name, region_name=aws_region_name)
    return bedrock_client


def get_model(model_id, model_parameter):
    llm = ChatBedrock(
        model_id=model_id,
        model_kwargs=model_parameter,
        client=bedrock_runtime
    )
    return llm


boto3_bedrock = get_bedrock_client(runtime=False)
bedrock_runtime = get_bedrock_client()


