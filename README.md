# Serverless Framework AWS Python Example

This template demonstrates how to deploy a Python function running on AWS Lambda using the traditional Serverless Framework. The deployed function does not include any event definitions as well as any kind of persistence (database). For more advanced configurations check out the [examples repo](https://github.com/serverless/examples/) which includes integrations with SQS, DynamoDB or examples of functions that are triggered in `cron`-like manner. For details about configuration of specific `events`, please refer to our [documentation](https://www.serverless.com/framework/docs/providers/aws/events/).

https://www.serverless.com/blog/handling-aws-lambda-python-dependencies
https://blog.richardkeller.net/building-a-pdf-generator-on-aws-lambda-with-python3-and-wkhtmltopdf/

## TODO
- EventBridge? to trigger monthly invoice events
- Write it up

## Usage

### Configure AWS

Use `export AWS_PROFILE=XXX` to set the profile before you run any actions like deploy

### Commands

```
sls deploy
sls invoke -f hello
sls invoke local --function hello
```

### Bundling dependencies

In case you would like to include third-party dependencies, you will need to use a plugin called `serverless-python-requirements`. You can set it up by running the following command:

```bash
sls plugin install -n serverless-python-requirements
```

Running the above will automatically add `serverless-python-requirements` to `plugins` section in your `serverless.yml` file and add it as a `devDependency` to `package.json` file. The `package.json` file will be automatically created if it doesn't exist beforehand. Now you will be able to add your dependencies to `requirements.txt` file (`Pipfile` and `pyproject.toml` is also supported but requires additional configuration) and they will be automatically injected to Lambda package during build process. For more details about the plugin's configuration, please refer to [official documentation](https://github.com/UnitedIncome/serverless-python-requirements).

### Troubleshooting

If config looks correct but still having deploy issues, manually delete CF stack and run `sls deploy` again

### Takeaways

- seems like can't get far evolving the stack without having to do nuclear deletes - likely more of a CloudFormation issue but still probably best to manage all related entities separately or more reliably (Terraform?)
- Serverless will generate wrapper `s_<function>` files and use these to set the handler
- filename containing the core lambda code has to be a certain length??? (see https://forum.serverless.com/t/serverless-sdk-get-user-handler-module-has-no-attribute/9659)
