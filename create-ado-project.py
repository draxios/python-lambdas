import json
import boto3
import base64
import urllib3

# Initialize AWS Secrets Manager client
secrets_client = boto3.client('secretsmanager')
http = urllib3.PoolManager()

def get_secret(secret_name):
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = response['SecretString']
        return json.loads(secret)
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise e

def check_project_exists(base_url, headers, project_name):
    url = f"{base_url}/_apis/projects?api-version=6.0"
    response = http.request('GET', url, headers=headers)
    projects = json.loads(response.data.decode('utf-8')).get('value', [])
    for project in projects:
        if project['name'] == project_name:
            return True
    return False

def create_project(base_url, headers, project_name, project_description):
    url = f"{base_url}/_apis/projects?api-version=6.0"
    body = {
        "name": project_name,
        "description": project_description,
        "capabilities": {
            "versioncontrol": {"sourceControlType": "Git"},
            "processTemplate": {"templateTypeId": "6b724908-ef14-45cf-84f8-768b5384da45"}
        }
    }
    response = http.request('POST', url, headers=headers, body=json.dumps(body))
    return response.status == 202

def configure_project(base_url, headers, project_name, project_owner):
    # Implement project configuration as needed
    pass

def disable_services(base_url, headers, project_id):
    features = ["ms.vss-work.agile", "ms.azure-artifacts.feature", "ms.vss-test-web.test"]
    for feature in features:
        url = f"{base_url}/_apis/FeatureManagement/FeatureStates/host/project/{project_id}/{feature}?api-version=6.0-preview.1"
        body = {"featureId": feature, "scope": {"userScoped": False, "settingScope": "project"}, "state": 0}
        response = http.request('PATCH', url, headers=headers, body=json.dumps(body))
        if response.status != 200:
            print(f"Failed to disable {feature} feature. Error: {response.data.decode('utf-8')}")

def lambda_handler(event, context):
    project_name = event['projectName']
    project_description = event.get('projectDescription', 'Project created via AWS Lambda')
    project_owner = event.get('projectOwner', 'IT-IS-BuildEngineers@stifel.com')
    
    secret_name = "your-secret-name"
    secrets = get_secret(secret_name)
    personal_access_token = secrets['AzureManagementPAT']
    
    base64_auth_info = base64.b64encode(f":{personal_access_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {base64_auth_info}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://dev.azure.com/StifelFinancial"
    
    # Check if the project already exists
    if check_project_exists(base_url, headers, project_name):
        return {
            "statusCode": 400,
            "body": json.dumps({"message": f"Project {project_name} already exists."})
        }
    
    # Create the new project
    if not create_project(base_url, headers, project_name, project_description):
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to create project."})
        }
    
    # Configure the project
    configure_project(base_url, headers, project_name, project_owner)
    
    # Get the project ID for disabling services
    url = f"{base_url}/_apis/projects/{project_name}?api-version=6.0"
    response = http.request('GET', url, headers=headers)
    project_id = json.loads(response.data.decode('utf-8'))['id']
    
    # Disable unwanted services
    disable_services(base_url, headers, project_id)
    
    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Project {project_name} created and configured successfully."})
    }
