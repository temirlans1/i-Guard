import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId)
import cv2
import time
import base64

os.environ["SENDGRID_API_KEY"] = "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"

def sendMail(file_path, timesec, to_mail):
    message = Mail(
        from_email='iguard@example.com',
        to_emails= to_mail,
        subject='IGuard: Обнаружено Нарушение',
        html_content="<strong>Обнаружено нарушение в {}</strong>".format(time.strftime('%H:%M:%S, %d.%m.%Y', time.localtime(timesec)))
        )

    with open(file_path, 'rb') as f:
        data = f.read()
        f.close()

    encoded = base64.b64encode(data).decode()
    attachment = Attachment()
    attachment.file_content = FileContent(encoded)
    attachment.file_type = FileType('image/jpg')
    attachment.file_name = FileName('ImageIGuard.jpg')
    message.attachment = attachment

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)
