import boto3
import json
import os
from awsmodule import AWSModule as Aws
from common import CommonClass as Com
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

#---------------------------------------------------------
# 各クラスの呼び出し
#---------------------------------------------------------
aws = Aws()
com = Com()

#---------------------------------------------------------
# 定数：
#---------------------------------------------------------
s3 = boto3.client('s3')

#-----------------------------------------------------------------------------------
# 定数：メール送信用
#-----------------------------------------------------------------------------------
email_jp_body="iam_jp.txt"
email_en_body="iam_en.txt"
assume_link_file="AssumeLink.json"


class EmailClass:

    def MailDataComposer(self, bucket, group_name):
        # S3からメール本文のテンプレートを取得
        # 日本語
        response = s3.get_object(Bucket = bucket, Key = email_jp_body)
        bodyJpMsg = response['Body'].read().decode('utf-8')
        # 英語
        response = s3.get_object(Bucket = bucket, Key = email_en_body)
        bodyEnMsg = response['Body'].read().decode('utf-8')

        # グループに紐づくAssumeRole名を設定
        attachJpBody = "AWSアカウント    AssumeRole名                   環境名称" + "\n"
        attachEnBody = "AWSAccount      AssumeRoleName                 Environment" + "\n"

        # S3からAssume_link.jsonを取得
        response = s3.get_object(Bucket = bucket, Key = assume_link_file)
        data = response['Body'].read()
        data_json = json.loads(data.decode('utf-8'))

        for dt_json in data_json:
            if group_name == dt_json["GroupArn"]:
                for atdt in dt_json["AssumeRole"]:
                    attachJpBody = attachJpBody + atdt.split('\n', 3)[2]            # AWSアカウント
                    attachJpBody = attachJpBody + "     "
                    attachJpBody = attachJpBody + atdt.split('\n', 3)[-1].ljust(30) # AssumeRole名
                    attachJpBody = attachJpBody + "     "
                    attachJpBody = attachJpBody + atdt.split('\n', 3)[1] + "\n"     # 環境名称

                    attachEnBody = attachEnBody + atdt.split('\n', 3)[2]            # AWSアカウント
                    attachEnBody = attachEnBody + "     "
                    attachEnBody = attachEnBody + atdt.split('\n', 3)[-1].ljust(30) # AssumeRole名
                    attachJpBody = attachJpBody + "     "
                    attachEnBody = attachEnBody + atdt.split('\n', 3)[0] + "\n"     # 環境名称

        bodyMsg = bodyJpMsg + "\n" + attachJpBody + "\n" + bodyEnMsg + "\n" + attachEnBody

        return bodyMsg

    # 送信するメール情報を作成する
    # SendEmail(mail_client, 送信元, 宛先, メールタイトル, メール本文, zipFilePath)
    def SendEmail(self, client, sender, to_email, subject, bodyMsg, zipFilePath):
        SENDER = sender
        RECIPIENT = to_email
        SUBJECT = subject
        BODY_TEXT = (bodyMsg)
        CHARSET = "UTF-8"
        ATTACHMENT = zipFilePath

        msg = MIMEMultipart("mixed")
        msg["Subject"] = SUBJECT
        msg["From"] = SENDER
        msg["To"] = RECIPIENT

        msg_body = MIMEMultipart('alternative')
        textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
        msg_body.attach(textpart)

        if zipFilePath is not None:
            att = MIMEApplication(open(zipFilePath, 'rb').read())
            att.add_header('Content-Disposition','attachment', filename=os.path.basename(ATTACHMENT))
        msg.attach(msg_body)
        if zipFilePath is not None:
            msg.attach(att)

        try:
            response = client.send_raw_email(
                Source=SENDER,
                Destinations=[
                    RECIPIENT,
                    SENDER
                ],
                RawMessage={
                    'Data':msg.as_string()
                }
            )
            print(response)

        except ClientError as e:
            print(e.response['Error']['Message'])
            return False

        return True