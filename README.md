# Stori test
## Index
1. [Objective](#objective)
2. [Requisites](#requisites)
3. [Architecture](#architecture)
4. [Procedure](#procedure)
5. [Schemas](#schemas)
6. [Lambdas and endpoints](#lambdas-and-endpoints)
7. [Driver Code](#driver-code)
8. [References](#references)

## Objective
Create a system that process Debit and Credit Transactions and send an
email summarizing the transactions by month and year.

ToDo: Send events to S3 Buckets, 
Add JWT or similar Security Measure,
Update date fields in transactions table to be not null
Prevent Duplicate Transactions

## Requisites
1. An AWS Account
2. [AWS CLI ver 2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. [Docker](https://docs.docker.com/get-docker)
4. Python

## Architecture
The architecture of the system were designed using AWS Lambdas and SNS to
propagate messages between lambdas that required it
![stori_architecture.png](stori_architecture.png)

## Procedure

The following sets of instructions describe the steps needed to develop the
mayor components of the system, follow them to add/update the functionalities

1. Set up an RDS instance
   - For a detailed Set of instructions visit [this tutorial](https://docs.aws.amazon.com/lambda/latest/dg/services-rds-tutorial.html)
   - Go to [Databases](https://console.aws.amazon.com/rds/home#databases:) and select "Create Database"
   - Choose MySQL (or what you prefer) and leave standard create
   - Set your credentials and the name of the database
   - **Set Public access to "Yes" inside Connectivity**
   - Set or create a VPC to the database, this will be used while in bootstrapping step if required
2. Bootstrapping a Lambda function
   - Command Line Login is required for the next steps
   - For a detailed procedure visit [this guide](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions)
   - Create a Dockerfile, take the following a an example
   - Crate a lambda script
   - Build the image, use ``` --platform linux/amd64``` if you are building from apple silicon
   - Use ```-f ./Dockerfile``` to specify the image build instructions
   - Log into your aws account through the CLI
   - Create a repository in Amazon ECR
   - Run the docker tag to tag your local image in ECR as the latest version
   - Create an [execution role](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-awscli.html#with-userapp-walkthrough-custom-events-create-iam-role) for the function if you dont have one already 
   - Run the docker push to deploy your image to the ECR repository
   - After deploying, visit your new [Lambda in AWS](https://us-east-1.console.aws.amazon.com/lambda)
   - Go to Configuration and set as VPC the one that is configured in your RDS instance (Omit if you require the lambda to access the internet)
   - Set Your environment variables if required

3. Updating a Lambda Function
   - In order to update the required lambda function, execute the following commands in the file directory
   - Substitute ```<repository_name>``` for your required repository
   - Replace ```<docker-image>:<tag>``` for your desired image and tag
   - Change ```<AWS_account_ID>``` with your AWS account ID.
   - Update ```<region>``` with your Lambda Region.
   - Command Line Login is required for the next steps
     - ``` 
       docker build --platform linux/amd64 -f ./Dockerfile -t <docker-image>:<tag> . 
       ```
     - ``` 
       docker tag send_email:dev \
       <AWS_account_ID>.dkr.ecr.<region>.amazonaws.com/<repository_name>:latest 
       ```
     - ```
       docker push \
       <AWS_account_ID>.dkr.ecr.<region>.amazonaws.com/<repository_name>:latest
       ```
4. Setting up SNS to Lambda-to-Lambda Communication
   - Create a SNS Topic
   - Publish messages in the topic
     - Go to [this question](https://repost.aws/knowledge-center/sns-topic-lambda) for a detailed set of instructions
     - Add permissions to Lambda (the VPC Role set in) to publish to the topic
     - Create an Amazon VPC endpoint following [this](https://docs.aws.amazon.com/sns/latest/dg/sns-vpc-tutorial.html) and [this](https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html#create-interface-endpoint)
     - [Allow internet Access to your publisher Lambda](https://repost.aws/knowledge-center/internet-access-lambda-function)
     - Add the [code snippet](https://repost.aws/knowledge-center/sns-topic-lambda) where you want the message to be sent
     - Go to your Lambda Function
     - Hit "Add destination" and then Select "Asynchronous invocation", "On success" and "SNS Topic"
     - Select your topic in the destination box and then Save the changes
   - Subscribe to messages in the Topic
     - For a detailed set of instructions [go here](https://docs.aws.amazon.com/sns/latest/dg/lambda-console.html)
     - Go to the SNS topic you created, hit "create subscription"
     - In Protocol Dropdown, select "AWS Lambda"
     - Copy and Paste the ARN of the subscriber lambda in the "Endpoint" box
     - Hit Create
     - Or
     - Go to your Lambda Function
     - Hit "Add Trigger" and then Select "SNS Topic"
     - Select your topic in the box and then Save the changes

5. Adding endpoint triggers to Lambda Function
   - Creating Endpoints
      - For a detailed set of instructions visit [this page](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-tutorial.html)
      - Go to [https://console.aws.amazon.com/apigateway] and hit "Create API", set it a name and save it
      - Choose "/" in resources tree, choose "Actions" and then "Create Resource"  
      - Set your new resource name (this will be part of the route to the resource)
      - Choose your new resource, then "Actions" and then "Create Method"
      - Select "ANY" or "POST" as you see fit
      - From "Integration Type" select "Lambda Function", then the region your lambda is, and then type the name of your lambda function
      - Hit Save
   - Create Stage
      - Repeat the former steps until you finish mapping your endpoints
      - Go to "Stages" in the API gateway Console tree
      - Select create, name your stage and select "[New Stage]" from the dropdown
      - Choose Create
   - Deploy
     - Go to "Resources" in the API gateway Console tree
     - Hit "Actions" and then "Deploy API"
     - Select your previously created Stage and optionally fill the description
     - Hit Deploy

## Schemas

### Client Schema

| Field Name     | Type    | Length | Not Null | Other    |
|----------------|---------|--------|----------|----------|
| ID             | INT     |        | True     | PK, AINC |
| Name           | varchar | 255    | False    |          |
| Email          | varchar | 255    | False    |          |
| Debit_balance  | decimal | 65,2   | True     |          |
| Credit_balance | decimal | 65,2   | True     |          |
*PK = Primary Key,
*AINC = Auto Increment

### Transaction Schema

| Field Name | Type     | Length | Not Null | Other    |
|------------|----------|--------|----------|----------|
| ID         | INT      |        | True     | PK, AINC |
| Client_id  | INT      |        | True     | FK       |
| Date       | DATETIME |        | False    |          |
| Type       | varchar  | 255    | False    |          |
| Ammount    | decimal  | 65,2   | True     |          |
*PK = Primary Key,
*AINC = Auto Increment,
*FK = Foreign key



## Lambdas and endpoints

### lambdas
| Endpoint            | status | Other                                 | Link     | Code                                         |
|---------------------|--------|---------------------------------------|----------|----------------------------------------------|
| create client       | done   |                                       | [Link](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/create_user_stori?tab=code) | [Link](lambda_functions/create_client)       |
| update client       | to do  |                                       |          |                                              |
| fetch clients       | done   | result only visible in Lambda console | [Link](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/fetch_users_stori?tab=code) | [Link](lambda_functions/fetch_clients)       |
| upload transactions | done   |                                       | [Link](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/upload_transactions_stori?tab=code) | [Link](lambda_functions/upload_transactions) |
| fetch transactions  | done   |                                       | [Link](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/fetch_transactions_stori?tab=code) | [Link](lambda_functions/fetch_transactions)  |
| send email          | done   | only invocable through SNS            | [Link](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/send_email_stori?tab=code) | [Link](lambda_functions/send_email)          |

### endpoints
1. Create user
    - endpoint:
        - https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/create_user
    - sample payload:
      ``` 
      { 
        "Email": "raul.sosa.cortes@gmail.com", "Name": "raul" 
      } 
      ```

2. Upload Transaction
   - endpoint:
     - https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/upload_transactions
   - sample payload:
     ``` 
       {
         "Date": "09/19/22 13:55:26",
         "Client_ID": 3,
         "Transaction": "Debit",
         "Amount": 0.55
       } 
     ```

3. Fetch Transactions
    - endpoint
      - https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/fetch_transactions
    - sample payload
       ```
       {
         "Client_ID": 3
       }
       ```
## Driver Code

head to the [Snippet folder](Snippet) and download the sample CSV.

Then download the `Snippet.py` code or copy the following,
run for testing the service
```
import json
import csv
import requests

cu_url = 'https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/create_user'
ut_url = 'https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/upload_transactions'
ft_url = 'https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/fetch_transactions'


cu_payload = {
    "Email": "raul.sosa.cortes@gmail.com",
    "Name": "raul"
}

response = requests.post(cu_url, json=cu_payload)
if(response.status_code==200):
    result = json.loads(response.text)
    client_id = result["id"]

    with open("transactions.csv", 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            ut_payload = {
                "Date": row[0],
                "Client_ID": client_id, # Uses Client ID instead of the one in the CSV
                "Transaction": row[2],
                "Amount": float(row[3])
            }

            ut_response = requests.post(ut_url, json=ut_payload)

    ft_payload={
      "Client_ID": client_id # Sends Mail to the Client We Updated
    }
    ft_response = requests.post(ft_url, json=ft_payload)

```



## References
[Setting up for Amazon RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SettingUp.html#sign-up-for-aws)

[Tutorial: Using a Lambda function to access Amazon RDS in an Amazon VPC](https://docs.aws.amazon.com/lambda/latest/dg/services-rds-tutorial.html)

[Deploy Python Lambda functions with container images](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions)

[Working with Lambda container images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)

[Using Lambda with the AWS CLI](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-awscli.html#with-userapp-walkthrough-custom-events-create-iam-role)

[Tutorial: Using Lambda with API Gateway](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-tutorial.html)

[How do I pass data through an API Gateway REST API to a backend Lambda function or HTTP endpoint?](https://repost.aws/knowledge-center/api-gateway-lambda-http-endpoint)

[Developing an HTTP API in API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop.html#http-api-examples)

[Why isn't Amazon SNS invoking my AWS Lambda function?](https://repost.aws/knowledge-center/sns-not-invoking-lambda)

[Monitoring Amazon SNS topics using CloudWatch](https://docs.aws.amazon.com/sns/latest/dg/sns-monitoring-using-cloudwatch.html)

[Can an AWS Lambda function call another?](https://stackoverflow.com/questions/31714788/can-an-aws-lambda-function-call-another?rq=3)

[Microservices Communications with AWS Lambda Invocation Types](https://medium.com/aws-serverless-microservices-with-patterns-best/microservices-communications-with-aws-lambda-invocation-types-aee2d6326866)

[Use sqs as an event source for lambda tutorial](https://aws.amazon.com/serverless/use-sqs-as-an-event-source-for-lambda-tutorial/)

[Subscribing a function to a topic](https://docs.aws.amazon.com/sns/latest/dg/lambda-console.html)

[Tutorial: Using AWS Lambda with Amazon Simple Notification Service](https://docs.aws.amazon.com/lambda/latest/dg/with-sns-example.html)

[Connecting AWS Lambdas To the Internet](https://stackoverflow.com/questions/37135725/aws-lambda-connecting-to-internet)

