from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pdfkit
from string import Template
from datetime import date
import datetime
from botocore.exceptions import ClientError

import boto3
import os

s3 = boto3.client('s3')
ses = boto3.client('ses')
ddb = boto3.client('dynamodb')

FMT = "%m/%d/%Y"
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
SENDER = "me@jpc2.org" # must be verified in AWS SES Email
CHARSET = "UTF-8"

# update this path if running locally
pdf_config = pdfkit.configuration(wkhtmltopdf="/opt/bin/wkhtmltopdf")

def handler(event, context):
    client_key = event["key"]

    #Increment client-specific counter for a new invoice
    invoice_count = get_invoice_count(client_key)
    padded = "{:06d}".format(invoice_count)
    invoice_number = f'{client_key}-{padded}'

    input = generate_invoice_html(event, invoice_number)
    filepath = f'/tmp/{invoice_number}.pdf'
    pdfkit.from_string(input, filepath, configuration=pdf_config, options={})

    # Upload to S3 Bucket
    s3.put_object(
        ACL='public-read',
        Body=open(filepath, 'rb'),
        ContentType='application/pdf',
        Bucket=S3_BUCKET_NAME,
        Key=f'{client_key}/{invoice_number}.pdf'
    )

    # Send Email and return response
    return send_email(to_emails=event["toEmails"], cc_emails=event.get("ccEmails"), subject=invoice_number, html=input,
                      text="New Invoice", tmp_file=filepath)

# TODO allow this to be overridden by the event parameters for custom invoicing
def get_html_params(invoice_number):
    today = date.today()
    lastMonth = today.replace(day=1) - datetime.timedelta(days=1)
    start = lastMonth.replace(day=1).strftime(FMT)
    end = lastMonth.strftime(FMT)

    return {"invoice_number": invoice_number, "invoice_date": today.strftime(FMT), "start": start, "end": end}

def generate_invoice_html(event, invoice_number):
    input_params = get_html_params(invoice_number)
    event.update(input_params)

    #convert line items to html first
    file = open('line_item.html', 'r')
    tmpl = file.read()
    line_item_html = ""
    for i in event.get("lineItems"):
        line_item_html += Template(tmpl).substitute(i)

    #add grand totals
    total = {
        "qty": "",
        "description": "<b>TOTAL</b>",
        "unitPrice": "",
        "amount": "<b>$" + str(sum(int(x.get("amount").replace("$", "")) for x in event.get("lineItems"))) + "</b>"
    }
    line_item_html += Template(tmpl).substitute(total)
    event["lineItemsHtml"] = line_item_html

    #do the full html transformation
    file = open('invoice_a360.html', 'r')
    return Template(file.read()).substitute(event)

def get_invoice_count(key):
    res = ddb.update_item(
        TableName='invoices',
        Key={
            "customer": {
                "S": key
            }
        },
        ReturnValues='UPDATED_NEW',
        UpdateExpression='SET invoice_count = invoice_count + :inc',
        ExpressionAttributeValues={
            ":inc": {
                "N": "1"
            }
        }
    )
    return int(res.get("Attributes").get("invoice_count").get("N"))

def send_email(to_emails, cc_emails, subject, html, text, tmp_file):
    response = {}
    destinations = to_emails
    try:
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = SENDER
        msg['To'] = ', '.join(to_emails)
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
            destinations = destinations + cc_emails

        # Create a multipart/alternative child container.
        msg_body = MIMEMultipart('alternative')
        textpart = MIMEText(text.encode(CHARSET), 'plain', CHARSET)
        htmlpart = MIMEText(html.encode(CHARSET), 'html', CHARSET)

        msg_body.attach(textpart)
        msg_body.attach(htmlpart)

        att = MIMEApplication(open(tmp_file, 'rb').read())
        att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(tmp_file))

        msg.attach(msg_body)
        msg.attach(att)

        response = ses.send_raw_email(
            Source=SENDER,
            Destinations=destinations,
            RawMessage={
                'Data': msg.as_string(),
            },
        )
        print(response)
    except ClientError as e:
        print("SES Error")
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

    response["statusCode"] = 200
    response["body"] = "body"
    return response

#custom event
# event = { "to": "Darrell Thompson", "toEmails": ["dthompson@mainstreamintegration.com"], "ccEmails": ["joe.conley@mainstreamintegration.com"], "company": "Maisntream Integration", "key": "MX", "address1": "19 Raintree Drive", "address2": "Sicklerville, NJ 08081", "lineItems": [ { "qty": 1, "description": "EJT Maintenance", "unitPrice": 200, "amount": 200 }, { "qty": 1, "description": "HMS Maintenance", "unitPrice": 200, "amount": 200 }, { "qty": 25, "description": "HMS Updates_120623", "unitPrice": 70, "amount": 1750 } ] }
# handler(event, None)
