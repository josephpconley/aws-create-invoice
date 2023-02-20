# Create a PDF Invoice using Serverless

Using Serverless to create a Lambda that generates a PDF, stores to S3 and sends via SES.  Uses a Lambda Layer with wkhtmltopdf for PDF generation

Links
- https://www.serverless.com/blog/handling-aws-lambda-python-dependencies
- https://blog.richardkeller.net/building-a-pdf-generator-on-aws-lambda-with-python3-and-wkhtmltopdf/

## Overview

![serverless](/create_invoice.svg)

## Usage

### Configure AWS

Use `export AWS_PROFILE=XXX` to set the profile before you run the following `sls` actions

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

### Takeaways

- If config looks correct but still having deploy issues, manually delete CF stack and run `sls deploy` again
- Wasted a lot of time trying to package wkhtmltopdf with this, using a shared Lambda Layer was really nice!
- seems like can't get far evolving the stack without having to do nuclear deletes - likely more of a CloudFormation issue but still probably best to manage all related entities separately or more reliably (Terraform?)
- Serverless will generate wrapper `s_<function>` files and use these to set the handler
- filename containing the core lambda code has to be a certain length??? (see https://forum.serverless.com/t/serverless-sdk-get-user-handler-module-has-no-attribute/9659)

## TODO
- EventBridge to trigger monthly invoice events
- Make more dynamic based on client and line items
- Write it up

### DDB queries

Simple update
```
aws dynamodb update-item --table-name invoices --key "S":"MX" 
```
