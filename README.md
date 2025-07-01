````markdown
# Sentiment Analysis Project: Your Feedback Analyzer

This document serves as a comprehensive guide for deploying a serverless sentiment analysis application on AWS. The project enables users to submit text feedback, which is then analyzed for sentiment and stored in a database, with results displayed via a web interface.

## Project Overview

The application operates through the following workflow:

* **User Input:** Text feedback is submitted via a simple web page.

* **API Invocation:** The frontend sends the input text to an AWS API Gateway endpoint.

* **Lambda Processing:** API Gateway triggers an AWS Lambda function.

* **Sentiment Analysis:** The Lambda function utilizes Amazon Comprehend to perform sentiment analysis on the provided text.

* **Data Persistence:** The original text, determined sentiment, and associated confidence scores are securely stored in an Amazon DynamoDB table.

* **Result Delivery:** The sentiment analysis results are returned to the frontend via API Gateway.

* **User Display:** The web page dynamically updates to display the analyzed sentiment.

## Prerequisites

To successfully deploy and operate this project, ensure you have:

* An active AWS Account.

* Access to the AWS Management Console.

* **AWS Command Line Interface (CLI)** installed and configured with appropriate credentials on your local machine. This is essential for executing the provided setup scripts.

* All project code files: `index.html`, `style.css`, `script.js`, and `lambda_function.py`.

## AWS Setup Procedures

This section outlines the steps to configure the necessary AWS resources. You can choose between two primary setup methods for most steps:

* **Option A: Manual Setup (AWS Console)** - Ideal for users who prefer a visual, step-by-step approach within the AWS Console.

* **Option B: CLI-Assisted Setup (Terminal Scripts)** - Recommended for users comfortable with command-line operations, offering a faster deployment process.

**Crucial Note:** Select a single AWS Region (e.g., `us-east-1`, `ap-south-1`) and use it consistently for all AWS services deployed in this project.

**Before proceeding with either option, define your configuration variables. Copy and paste the following into your terminal and execute it once:**

```bash
# --- Configuration Variables (Update these values) ---
# IMPORTANT: Ensure these match your AWS setup and desired resource names.
AWS_REGION="YOUR_AWS_REGION" # Example: us-east-1, ap-south-1
AWS_ACCOUNT_ID="YOUR_ACCOUNT_ID" # Your 12-digit AWS Account ID

# Resource Names (can be customized, but ensure consistency)
LAMBDA_ROLE_NAME="SentimentAnalysisLambdaRole"
DYNAMODB_TABLE_NAME="SentimentAnalysisResults"
LAMBDA_FUNCTION_NAME="SentimentAnalysisFunction"
API_GATEWAY_NAME="SentimentAnalysisAPI"
API_GATEWAY_ROUTE_PATH="/analyze"

echo "Configuration variables have been set. Proceed with the setup steps below."
````

-----

### 1\. Create IAM Role for Lambda Permissions

This role grants your Lambda function the necessary permissions to interact with other AWS services.

**Option A: Manual Setup (AWS Console)**

  * Navigate to the **IAM Console** \> **Roles**.

  * Click **Create role**.

  * For "Trusted entity type", select "AWS service", then choose "Lambda" from the use case dropdown.

  * Proceed to "Add permissions". Search for and attach the following managed policies:

      * `AWSLambdaBasicExecutionRole` (Enables logging to CloudWatch).

      * `AmazonDynamoDBFullAccess` (Allows read/write access to DynamoDB).

      * `ComprehendFullAccess` (Grants permission to call Amazon Comprehend).

  * Click "Next".

  * **Name the role:** `SentimentAnalysisLambdaRole`.

  * Click **Create role**.

**Option B: CLI Script (Terminal)**

```bash
echo "Initiating IAM Role creation: ${LAMBDA_ROLE_NAME}..."
aws iam create-role \
  --role-name "${LAMBDA_ROLE_NAME}" \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }' \
  --region "${AWS_REGION}"

echo "Attaching required policies to role: ${LAMBDA_ROLE_NAME}..."
aws iam attach-role-policy --role-name "${LAMBDA_ROLE_NAME}" --policy-arn "arn:aws:iam::aws:policy/AWSLambdaBasicExecutionRole" --region "${AWS_REGION}"
aws iam attach-role-policy --role-name "${LAMBDA_ROLE_NAME}" --policy-arn "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess" --region "${AWS_REGION}"
aws iam attach-role-policy --role-name "${LAMBDA_ROLE_NAME}" --policy-arn "arn:aws:iam::aws:policy/ComprehendFullAccess" --region "${AWS_REGION}"

LAMBDA_ROLE_ARN=$(aws iam get-role --role-name "${LAMBDA_ROLE_NAME}" --query 'Role.Arn' --output text --region "${AWS_REGION}")
echo "IAM Role ARN: ${LAMBDA_ROLE_ARN}"
echo "IAM Role creation and policy attachment complete."
```

-----

### 2\. Create DynamoDB Table

This table will serve as your database for storing sentiment analysis results.

**Option A: Manual Setup (AWS Console)**

  * Navigate to the **DynamoDB Console** \> **Tables**.

  * Click **Create table**.

  * **Table name:** Enter `SentimentAnalysisResults`. (This name **must** precisely match the table name specified in your `lambda_function.py` code).

  * **Partition key:** Enter `id` (ensure "String" is selected as the type).

  * Click **Create table**.

**Option B: CLI Script (Terminal)**

```bash
echo "Initiating DynamoDB Table creation: ${DYNAMODB_TABLE_NAME}..."
aws dynamodb create-table \
  --table-name "${DYNAMODB_TABLE_NAME}" \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region "${AWS_REGION}"

echo "Waiting for DynamoDB table to become active. This may take a moment..."
aws dynamodb wait table-exists --table-name "${DYNAMODB_TABLE_NAME}" --region "${AWS_REGION}"
echo "DynamoDB table ${DYNAMODB_TABLE_NAME} is now active."
```

-----

### 3\. Create Lambda Function & Upload Code

This step involves creating the Lambda function and deploying your Python backend code. **This step requires manual interaction in the AWS Console.**

**Manual Setup (AWS Console - REQUIRED):**

1.  Navigate to the **Lambda Console** \> **Create function**.

2.  Choose "Author from scratch".

3.  **Function name:** Enter `SentimentAnalysisFunction`. (Use this exact name for consistency with later steps).

4.  **Runtime:** Select `Python 3.9` (or a newer Python version if available).

5.  **Execution role:** Choose "Use an existing role" and select the `SentimentAnalysisLambdaRole` you created in Step 1.

6.  Click **Create function**.

7.  Once the function is created, go to its "Code" tab.

8.  **Replace the entire content of the default `lambda_function.py` file with your project's `lambda_function.py` code.**

9.  Click **"Deploy"** to save and deploy your code changes.

10. Go to the **"Configuration"** tab, then "General configuration". Click "Edit".

      * **Memory:** Set to `256 MB` (or `512 MB` for potentially faster execution).

      * **Timeout:** Set to `30 seconds` (to allow sufficient time for Comprehend analysis).

      * Click **"Save"**.

-----

### 4\. Create API Gateway HTTP API

This establishes the public HTTP endpoint for your frontend to communicate with your Lambda function.

**Option A: Manual Setup (AWS Console)**

  * Navigate to the **API Gateway Console** \> **Create API**.

  * Select **"HTTP API"** and click "Build".

  * **API name:** Enter `SentimentAnalysisAPI`.

  * Click "Next".

  * **Configure Routes:**

      * **Method:** Select `POST`.

      * **Path:** Enter `/analyze`.

  * Click "Next".

  * **Define Integrations:**

      * **Integration target:** Select `Lambda function`.

      * **Lambda function:** Choose `SentimentAnalysisFunction` from the dropdown.

  * Click "Next", then **Review and Create**.

**Option B: CLI Script (Terminal)**

```bash
echo "Initiating API Gateway HTTP API creation: ${API_GATEWAY_NAME}..."
API_ID=$(aws apigatewayv2 create-api \
  --name "${API_GATEWAY_NAME}" \
  --protocol-type HTTP \
  --query 'ApiId' --output text \
  --region "${AWS_REGION}")
echo "API Gateway ID: ${API_ID}"
echo "API Gateway created."
```

-----

### 5\. Create API Gateway Integration

This connects your newly created API Gateway to your Lambda function.

**Option A: Manual Setup (AWS Console)**

  * If you followed the manual steps for API Gateway creation (Step 4), this integration was likely configured as part of that process. Verify that your `POST /analyze` route is correctly integrated with your `SentimentAnalysisFunction`.

**Option B: CLI Script (Terminal)**

```bash
echo "Creating API Gateway integration with Lambda function..."
LAMBDA_FUNCTION_ARN=$(aws lambda get-function --function-name "${LAMBDA_FUNCTION_NAME}" --query 'Configuration.FunctionArn' --output text --region "${AWS_REGION}")
API_ID=$(aws apigatewayv2 get-apis --name "${API_GATEWAY_NAME}" --query 'Items[0].ApiId' --output text --region "${AWS_REGION}")

INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "${API_ID}" \
  --integration-type AWS_PROXY \
  --integration-method POST \
  --integration-uri "${LAMBDA_FUNCTION_ARN}" \
  --payload-format-version 1.0 \
  --query 'IntegrationId' --output text \
  --region "${AWS_REGION}")
echo "Integration ID: ${INTEGRATION_ID}"
echo "API Gateway Integration created."
```

-----

### 6\. Create API Gateway Route & Stage

This defines the specific URL path for your API and deploys it to a stage.

**Option A: Manual Setup (AWS Console)**

  * If you followed the manual steps for API Gateway creation (Step 4), the `POST /analyze` route should already be defined, and a `$default` stage should have been automatically deployed.

**Option B: CLI Script (Terminal)**

```bash
echo "Creating API Gateway route: POST ${API_GATEWAY_ROUTE_PATH}..."
API_ID=$(aws apigatewayv2 get-apis --name "${API_GATEWAY_NAME}" --query 'Items[0].ApiId' --output text --region "${AWS_REGION}")
INTEGRATION_ID=$(aws apigatewayv2 get-integrations --api-id "${API_ID}" --query 'Items[0].IntegrationId' --output text --region "${AWS_REGION}")

ROUTE_ID=$(aws apigatewayv2 create-route \
  --api-id "${API_ID}" \
  --route-key "POST ${API_GATEWAY_ROUTE_PATH}" \
  --target "integrations/${INTEGRATION_ID}" \
  --query 'RouteId' --output text \
  --region "${AWS_REGION}")
echo "Route ID: ${ROUTE_ID}"

echo "Creating API Gateway stage: $default..."
aws apigatewayv2 create-stage \
  --api-id "${API_ID}" \
  --stage-name '$default' \
  --auto-deploy \
  --region "${AWS_REGION}"
echo "API Gateway Route and Stage created."
```

-----

### 7\. Grant API Gateway Lambda Invoke Permission

This permission allows API Gateway to trigger your Lambda function when a request is received.

**Option A: Manual Setup (AWS Console)**

  * AWS typically configures this permission automatically when you integrate Lambda with API Gateway. To verify, navigate to your `SentimentAnalysisFunction` in the Lambda Console. Under the "Configuration" tab, then "Permissions", look for a resource-based policy statement that grants `apigateway.amazonaws.com` permission to invoke your function.

**Option B: CLI Script (Terminal)**

```bash
echo "Granting API Gateway permission to invoke Lambda function..."
API_ID=$(aws apigatewayv2 get-apis --name "${API_GATEWAY_NAME}" --query 'Items[0].ApiId' --output text --region "${AWS_REGION}")
LAMBDA_FUNCTION_ARN=$(aws lambda get-function --function-name "${LAMBDA_FUNCTION_NAME}" --query 'Configuration.FunctionArn' --output text --region "${AWS_REGION}")

aws lambda add-permission \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --statement-id "AllowAPIGatewayInvoke" \
  --action "lambda:InvokeFunction" \
  --principal "apigateway.amazonaws.com" \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*${API_GATEWAY_ROUTE_PATH}" \
  --region "${AWS_REGION}"
echo "Lambda invoke permission granted to API Gateway."
```

-----

### 8\. Configure API Gateway CORS

Cross-Origin Resource Sharing (CORS) settings are crucial for your frontend (served from a different origin, e.g., `localhost`) to successfully make requests to your API.

**Option A: Manual Setup (AWS Console)**

  * In the API Gateway Console, select your `SentimentAnalysisAPI`.

  * Navigate to the **CORS** section.

  * **Access-Control-Allow-Headers:** Add `Content-Type`.

  * **Access-Control-Allow-Methods:** Select `POST` and `OPTIONS`.

  * **Access-Control-Allow-Origin:** Enter `*` (This allows requests from any origin, suitable for development. For production, replace `*` with your specific frontend domain, e.g., `https://your-domain.com`).

  * Click **Save**.

**Option B: CLI Script (Terminal)**

```bash
echo "Configuring CORS for API Gateway..."
API_ID=$(aws apigatewayv2 get-apis --name "${API_GATEWAY_NAME}" --query 'Items[0].ApiId' --output text --region "${AWS_REGION}")

aws apigatewayv2 update-api \
  --api-id "${API_ID}" \
  --cors-configuration '{"AllowOrigins":["*"],"AllowHeaders":["Content-Type"],"AllowMethods":["OPTIONS","POST"],"MaxAge":300}' \
  --region "${AWS_REGION}"
echo "CORS configured for API Gateway."
```

-----

### 9\. Retrieve Final API URL

This step retrieves the complete URL of your deployed API endpoint, which you'll use in your frontend.

**Option A: Manual Setup (AWS Console)**

  * In the API Gateway Console, select your `SentimentAnalysisAPI`. The "Invoke URL" is displayed prominently at the top of its summary page. Copy this URL and append `/analyze` to it.

**Option B: CLI Script (Terminal)**

```bash
echo "Retrieving API Gateway Invoke URL..."
API_ID=$(aws apigatewayv2 get-apis --name "${API_GATEWAY_NAME}" --query 'Items[0].ApiId' --output text --region "${AWS_REGION}")

INVOKE_URL=$(aws apigatewayv2 get-apis \
  --api-id "${API_ID}" \
  --query 'Items[0].ApiEndpoint' --output text \
  --region "${AWS_REGION}")
FULL_API_URL="${INVOKE_URL}${API_GATEWAY_ROUTE_PATH}"

echo ""
echo "--- AWS SETUP COMPLETE! ---"
echo "Your API Gateway Invoke URL is: ${FULL_API_URL}"
echo "--------------------------"
```

### Part 5: Frontend Configuration & Local Execution

Now, let's connect your web page to your newly deployed API and run it locally.

1.  **Open your local `index.html` file** in a code editor.

2.  **Locate the `apiUrl` constant:** Find the line `const apiUrl = '...';` within the `<script>` section of your `index.html`.

3.  **Update the URL:** **Replace the placeholder URL with the `FULL_API_URL`** that was displayed in your terminal after running Step 9 (or retrieved manually).

      * Example: `const apiUrl = 'https://YOUR_API_GATEWAY_ID.execute-api.YOUR_REGION.amazonaws.com/analyze';`

4.  **Save `index.html`.**

5.  **Run your frontend:** Open `index.html` directly in your web browser. For a more robust local development experience, consider using a "Live Server" extension in VS Code.

## Testing the Application

To confirm your application is fully operational:

  * Open your `index.html` file in a web browser.

  * Enter various text inputs into the feedback box (e.g., "This is a great day\!", "I am very disappointed.", "It's okay.").

  * Click the "Analyze Sentiment" button.

  * Observe the displayed sentiment results and confidence scores on the page.

  * Verify that new entries, corresponding to your submitted text and analysis results, appear in your `SentimentAnalysisResults` table within the DynamoDB console.

## Cleaning Up AWS Resources

To prevent incurring unnecessary charges, it is crucial to delete all AWS resources created for this project once you have finished experimenting.

1.  **Delete API Gateway API:** Navigate to API Gateway, select `SentimentAnalysisAPI`, and proceed with deletion.

2.  **Delete Lambda Function:** Navigate to Lambda, select `SentimentAnalysisFunction`, and proceed with deletion.

3.  **Delete DynamoDB Table:** Navigate to DynamoDB, select `SentimentAnalysisResults`, and proceed with deletion.

4.  **Delete IAM Role:** Navigate to IAM, select `SentimentAnalysisLambdaRole`, and proceed with deletion. (Note: You may need to manually detach any attached policies from the role before it can be deleted, if AWS does not do so automatically).

<!-- end list -->

```
```