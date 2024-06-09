import json
import os
import boto3
import requests

def lambda_handler(event, context):
    secret_name = "TerraformEnterpriseToken"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    client = boto3.client('secretsmanager', region_name=region_name)

    # Retrieve the secret
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(get_secret_value_response['SecretString'])

    token = secret['token']
    organization = "your_terraform_organization"
    workspace_name = event['workspace_name']
    url = f"https://app.terraform.io/api/v2/organizations/{organization}/workspaces"

    headers = {
        'Content-Type': 'application/vnd.api+json',
        'Authorization': f'Bearer {token}'
    }

    payload = {
        "data": {
            "attributes": {
                "name": workspace_name,
                "terraform_version": "1.0.0"
            },
            "type": "workspaces"
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return {
        'statusCode': response.status_code,
        'body': json.dumps(response.json())
    }
