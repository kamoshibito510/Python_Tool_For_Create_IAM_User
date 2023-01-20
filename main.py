import boto3
import csv
import urllib.parse
from awsmodule import AWSModule as Aws
from common import CommonClass as Com
from emailmodule import EmailClass as Email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

#---------------------------------------------------------
# 各クラスの呼び出し
#---------------------------------------------------------
aws = Aws()
com = Com()
email = Email()

#---------------------------------------------------------
# 定数：
#---------------------------------------------------------
s3 = boto3.client('s3')

#-----------------------------------------------------------------------------------
# 定数：メール送信用
#-----------------------------------------------------------------------------------
email1_title="AWS IAM User Information"
email2_title="Password of attached file"
email2_path="pass.txt"
from_email = "{mail_address}"
#-----------------------------------------------------------------------------------

def lambda_handler(event, context):

    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        obj_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

        response = s3.get_object(Bucket=bucket, Key=obj_key)
        csv_data = response['Body'].read().decode('shift-jis').splitlines()
        reader = csv.reader(csv_data)
        # ヘッダー行スキップ
        next(reader)
        # ユーザー毎のループ処理
        for line in reader:
            # ユーザー作成～メール送信用変数
            to_email = line[0]
            name_prefix = line[1]
            ticket_no = line[2]
            group_name = line[3]
            add_group = ["All_Users", line[3]]

            # ユーザー名を作成
            user_name = "{}_{}".format(name_prefix, to_email.replace("@","__"))

            # IAMのクライアント作成
            iam = aws.CreateIAMClient()

            # # IAMユーザー存在チェック
            response = aws.CheckCreateUser(iam, user_name)
            if (response == True):
                # 次ループへ
                continue

            # # ユーザー作成
            response = aws.CreateUser(iam, user_name)

            # # ユーザーをグループに追加
            for group in add_group:
                response = aws.AddUserToGroup(iam,  group, user_name)

            # ランダムパスワード生成
            size = 12
            password = com.KeyGenerator(size)

            # ユーザーのパスワードを設定＆ログイン時パスワード変更
            response = aws.CreateLoginProfile(iam, user_name, password, True)

            # メール送信用クライアント作成
            mail_client = aws.CreateEmailClient()

            # メール本文を作成
            bodyMsg = email.MailDataComposer(bucket, group_name)

            # CSVファイルをＺＩＰ化
            zipFilePath = com.CsvZipfileComposer(user_name, password, bucket)

            # メールを送信する
            response = email.SendEmail(mail_client, from_email, to_email, email1_title, bodyMsg, zipFilePath)

            if response:
                print("SendEmail To:{}".format(to_email))

                # メール送信できた場合パスワード通知も送信する
                # 共通で使用するパスワードメール本文を取得する
                response = s3.get_object(Bucket = bucket, Key = email2_path)
                bodyMsg = response['Body'].read().decode('utf-8')
                # メールを送信する
                response = email.SendEmail(mail_client, from_email, to_email, email2_title, bodyMsg, None)

            if response:
                print("SendEmail for password To:{}".format(to_email))

    except Exception as e:
        raise e




