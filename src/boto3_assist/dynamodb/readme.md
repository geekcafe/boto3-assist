# DynamoDB Library



## Debugging Locally with Docker

Make sure you have Docker installed and it's running before completing the following steps.

### Steps to Run DynamoDB Local with Docker
1. Pull the DynamoDB Local Docker Image:

- Open a terminal or command prompt and run the following command to pull the DynamoDB Local Docker image from the Docker Hub:


```sh
docker pull amazon/dynamodb-local
```

2. Run the DynamoDB Local Docker Container:

- To start a container with DynamoDB Local, use the following command:


```sh
docker run -d -p 8000:8000 amazon/dynamodb-local
```


- This command runs the container in detached mode (-d) and maps port 8000 of the container to port 8000 on your local machine (-p 8000:8000).

3. Verify the Container is Running:

- You can check if the container is running with the following command:

```sh
docker ps
```

- You should see the `amazon/dynamodb-local` container listed.

4. Configure AWS CLI or SDKs to Use Local DynamoDB:

- When using AWS CLI:

```sh
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

- When using AWS SDKs in your application, set the endpoint to <http://localhost:8000.> For example, in Python using Boto3:


```python
import boto3
dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
```
- 



```sh
docker run -d --name scylla-dynamodb \
  -p 8000:8000 \
  scylladb/scylla --alternator-port=8000 \
  --alternator-write-isolation=always_use_lwt \
  --developer-mode 1


```