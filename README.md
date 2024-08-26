# boto3 assist

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

