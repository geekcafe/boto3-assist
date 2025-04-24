# boto3 assist

[![PyPI version](https://img.shields.io/pypi/v/boto3-assist.svg)](https://pypi.org/project/boto3-assist/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/boto3-assist)](https://pepy.tech/project/boto3-assist)

This is in beta and subject to changes before it's initial 1.0.0 release

This libary was created to make life a little easier when using boto3.

Currently it supports:
- User Authentication / Session Mapping
- DynamoDB model mapping and key generation.


## User Authentication / Session Mapping
Have you ever needed an easy way to load your sessions for a local, dev or production enviroment? Well this library
makes it a little easier by lazy loading your boto3 session so that tools like `python-dotenv` can be used to load your
environment vars first and then load your session.

## DyamoDB model mapping and Key Generation
It's a light weight mapping tool to turn your python classes / object models to DynamoDB items that are ready
for saving.  See the [examples](https://github.com/geekcafe/boto3-assist/tree/main/examples) directory in the repo for more information.


```sh
python -m vevn .venv
source ./.venv/bin/activate

pip install --upgrade pip  
pip install boto3-assist

```

## Running Unit Tests
Several of our tests use a mocking library to simulate connections to S3, DynamoDB, etc.  In order to use those tests, you will need to have a `.env.unittest` file at the root of this project (which our tests will attempt to locate and load).  

For your convenince the `.evn.unittest` file has been added to this project.  The values should not point to live AWS profiles, instead it should use the values added.

Since we also point to a profile, you should create the profile in the `~/.aws/config` file.  The entry should look like the following:

```toml
[profile moto-mock-tests]
region = us-east-1
output = json
aws_access_key_id = test
aws_secret_access_key = test

```

