import json

import boto3
from botocore.exceptions import ClientError

# Step1: Create IAM Roles: `Dev` and `User`
# Initialize the IAM client
iam_client = boto3.client('iam')


# Create Dev role
def create_iam_role(role_name, assume_role_policy_document):
    try:
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document)
        )
        print(f"Created Role: {role['Role']['Arn']}")
        return role['Role']
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"Role '{role_name}' already exists.")
            try:
                existing_role = iam_client.get_role(RoleName=role_name)
                return existing_role['Role']
            except ClientError as fetch_error:
                print(f"Error fetching existing role '{role_name}': {fetch_error}")
                return None
        else:
            print(f"Error creating role '{role_name}': {e}")
            return None


dev_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "arn:aws:iam::891377242643:root"},
            "Action": "sts:AssumeRole"
        }
    ]
}

dev_role = create_iam_role("Dev", dev_role_policy)

# Create User role
user_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "arn:aws:iam::891377242643:root"},
            "Action": "sts:AssumeRole"
        }
    ]
}

user_role = create_iam_role("User", user_role_policy)

# Step2: Attach IAM Policies to Roles
# Attach full S3 access to Dev role
iam_client.attach_role_policy(
    RoleName="Dev",
    PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
)

# Attach restricted S3 list/get access to User role
user_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket", "s3:GetObject"],
            "Resource": "*"
        }
    ]
}

iam_client.put_role_policy(
    RoleName="User",
    PolicyName="S3ListGetAccess",
    PolicyDocument=json.dumps(user_policy_document)
)

# Step3: Create IAM User
# Create a new IAM user
iam_client = boto3.client('iam')


def create_iam_user(user):
    try:
        iam_user_obj = iam_client.create_user(UserName=user)
        print(f"Created user {user}")
        return iam_user_obj['User']
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"User '{user}' already exists.")
            try:
                existing_user = iam_client.get_user(UserName=user)
                return existing_user['User']
            except ClientError as fetch_error:
                print(f"Error fetching existing user '{user}': {fetch_error}")
                return None
        else:
            print(f"Error creating user '{user}': {e}")
            return None


user_name = 'TestUser'
iam_user = create_iam_user(user_name)

# Define the policy that only allows the `TestUser` to assume `Dev` and `User`
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": [
                "arn:aws:iam::891377242643:role/Dev",
                "arn:aws:iam::891377242643:role/User"
            ]
        }
    ]
}

# Attach the custom policy to `TestUser`
iam_client.put_user_policy(
    UserName=user_name,
    PolicyName="AssumeDevUserRoles",
    PolicyDocument=json.dumps(assume_role_policy)
)

# Step4: Assume the `Dev` Role and Create S3 Buckets and Objects
sts_client = boto3.client('sts')

# Assume the Dev role
dev_role_arn = dev_role['Arn']
dev_credentials = sts_client.assume_role(
    RoleArn=dev_role_arn,
    RoleSessionName="DevSession"
)

# Create a session with the assumed role's temporary credentials
session = boto3.Session(
    aws_access_key_id=dev_credentials['Credentials']['AccessKeyId'],
    aws_secret_access_key=dev_credentials['Credentials']['SecretAccessKey'],
    aws_session_token=dev_credentials['Credentials']['SessionToken'],
    region_name='us-west-2'
)

# Initialize S3 client using the session
s3_dev = session.client('s3')

# Create S3 bucket 'lecture1' in us-east-1
bucket_name = 'shuwen-6620-lecture1'
region = 'us-west-2'

try:
    s3_dev.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': region}
    )
    print(f"Bucket '{bucket_name}' created successfully in '{region}'")
except ClientError as e:
    print(f"Error creating bucket: {e}")

# Create objects in the bucket
assignment1_content = 'Empty Assignment 1'
assignment2_content = 'Empty Assignment 2'
s3_dev.put_object(Bucket=bucket_name, Key='assignment1.txt', Body=assignment1_content)
s3_dev.put_object(Bucket=bucket_name, Key='assignment2.txt', Body=assignment2_content)

# Upload an image
with open('recording1.jpg', 'rb') as img_file:
    s3_dev.put_object(Bucket=bucket_name, Key='recording1.jpg', Body=img_file)

# Step5: Assume the `User` Role and Compute Total Size of Assignment Objects
# Assume the User role
user_role_arn = user_role['Arn']
user_credentials = sts_client.assume_role(
    RoleArn=user_role_arn,
    RoleSessionName="UserSession"
)

# Create a session with the assumed role's temporary credentials
session = boto3.Session(
    aws_access_key_id=user_credentials['Credentials']['AccessKeyId'],
    aws_secret_access_key=user_credentials['Credentials']['SecretAccessKey'],
    aws_session_token=user_credentials['Credentials']['SessionToken'],
    region_name='us-west-2'
)

# Initialize S3 client using the session
s3_user = session.client('s3')

# List all objects with prefix 'assignment'
response = s3_user.list_objects_v2(Bucket=bucket_name, Prefix='assignment')
objects = response.get('Contents', [])
total_size = sum(obj['Size'] for obj in objects)
print(f"Total size of assignment objects: {total_size} bytes")

# Step6: Assume the `Dev` Role and Delete Objects and Bucket
# Assume Dev role again
dev_credentials = sts_client.assume_role(
    RoleArn=dev_role_arn,
    RoleSessionName="DevSession2"
)

# Create a session with the assumed role's temporary credentials
session = boto3.Session(
    aws_access_key_id=dev_credentials['Credentials']['AccessKeyId'],
    aws_secret_access_key=dev_credentials['Credentials']['SecretAccessKey'],
    aws_session_token=dev_credentials['Credentials']['SessionToken'],
    region_name='us-west-2'
)

# Initialize S3 client using the session
s3_dev = session.client('s3')

# Delete all objects in the bucket
response2 = s3_dev.list_objects_v2(Bucket=bucket_name)
all_objects = response2.get('Contents', [])
for obj in all_objects:
    s3_dev.delete_object(Bucket=bucket_name, Key=obj['Key'])

# Delete the bucket
s3_dev.delete_bucket(Bucket=bucket_name)
print(f"Deleted bucket {bucket_name} and all objects")
