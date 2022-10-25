import boto3

def notify():
    client = boto3.client('ses')
    response = client.send_email(
        Destination={
            'ToAddresses': [
                'cbonnette215@gmail.com'
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': '<h1>TradeForge Order</h1><p>This is a pretty mail with HTML formatting</p>',
                },
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': 'This is for those who cannot read HTML.',
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': 'TradeForge Notification',
            },
        },
        Source='cbonnette215@gmail.com',
    )