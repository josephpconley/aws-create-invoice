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

FMT = "%m/%d/%Y"
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
SENDER = "me@jpc2.org" # must be verified in AWS SES Email
RECIPIENT = "joe.conley@mainstreamintegration.com" # must be verified in AWS SES Email
CHARSET = "UTF-8"

def handler(event, context):
    pdf_config = pdfkit.configuration(wkhtmltopdf="/opt/bin/wkhtmltopdf")

    today = date.today()
    lastMonth = today.replace(day=1) - datetime.timedelta(days=1)
    start = lastMonth.replace(day=1).strftime(FMT)
    end = lastMonth.strftime(FMT)
    invoice_number = "MX-000103"
    key = "MX/" + invoice_number + '.pdf'
    filepath = '/tmp/{invoice_number}.pdf'.format(invoice_number=invoice_number)

    d = {"invoice_number": invoice_number, "invoice_date": today.strftime(FMT), "start": start, "end": end}
    file = open('mx.html', 'r')
    input = Template(file.read()).substitute(d)
    pdfkit.from_string(input, filepath, configuration=pdf_config, options={})

    # Upload to S3 Bucket
    r = s3.put_object(
        ACL='public-read',
        Body=open(filepath, 'rb'),
        ContentType='application/pdf',
        Bucket=S3_BUCKET_NAME,
        Key=key
    )

    # Format the PDF URI
    object_url = "https://{0}.s3.amazonaws.com/{1}".format(S3_BUCKET_NAME, key)
    return send_email(subject=invoice_number, html=input, text="New Invoice", tmp_file=filepath)

def send_email(subject, html, text, tmp_file):
    response = {}
    # Try to send the email.
    try:
        # Create a multipart/mixed parent container.
        msg = MIMEMultipart('mixed')
        # Add subject, from and to lines.
        msg['Subject'] = subject
        msg['From'] = SENDER
        msg['To'] = RECIPIENT

        # Create a multipart/alternative child container.
        msg_body = MIMEMultipart('alternative')

        # Encode the text and HTML content and set the character encoding. This step is
        # necessary if you're sending a message with characters outside the ASCII range.
        textpart = MIMEText(text.encode(CHARSET), 'plain', CHARSET)
        htmlpart = MIMEText(html.encode(CHARSET), 'html', CHARSET)

        # Add the text and HTML parts to the child container.
        msg_body.attach(textpart)
        msg_body.attach(htmlpart)

        # Define the attachment part and encode it using MIMEApplication.
        att = MIMEApplication(open(tmp_file, 'rb').read())

        # Add a header to tell the email client to treat this part as an attachment,
        # and to give the attachment a name.
        att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(tmp_file))

        # Attach the multipart/alternative child container to the multipart/mixed
        # parent container.
        msg.attach(msg_body)

        # Add the attachment to the parent container.
        msg.attach(att)

        #Provide the contents of the email.
        response = ses.send_raw_email(
            Source=SENDER,
            Destinations=[RECIPIENT],
            RawMessage={
                'Data': msg.as_string(),
            },
        )
        # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

    response["statusCode"] = 200
    response["body"] = "body"
    return response
