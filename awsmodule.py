import boto3
import configparser
from boto3.session import Session



class AWSModule:
    def __init__(self):
        self.aws_access_key_id = None
        self.aws_secret_access_key = None
        self.aws_session_token = None

    def CreateIAMClient(self):
        # aws_configファイルの読み込み
        aws_config = configparser.ConfigParser()
        aws_config.read('./aws_config.ini')

        dest_prefix = "master"
        dest_region = "us-east-1"

        # クロスアカウントのクライアント作成
        role_arn = aws_config["profile " + dest_prefix]["role_arn"]
        endpoint_url = "https://sts." + dest_region + ".amazonaws.com"
        sts = boto3.client("sts", region_name = dest_region, endpoint_url = endpoint_url)
        cross_account = sts.assume_role(
        RoleArn = role_arn,
        RoleSessionName = "cross_account_" + dest_prefix
        )
        # Credentialsの取得
        cross_access_key = cross_account["Credentials"]["AccessKeyId"]
        cross_secret_key = cross_account["Credentials"]["SecretAccessKey"]
        cross_settion_token = cross_account["Credentials"]["SessionToken"]
        # クロスアカウントでsession取得
        session = Session(
        aws_access_key_id = cross_access_key,
        aws_secret_access_key = cross_secret_key,
        aws_session_token = cross_settion_token,
        region_name = dest_region
        )
        iam = session.client("iam", region_name = dest_region)

        return iam

    def CreateEmailClient(self):
        # aws_configファイルの読み込み
        aws_config = configparser.ConfigParser()
        aws_config.read('./aws_config.ini')

        dest_prefix = "cicd1"
        dest_region = "ap-northeast-1"

        # クロスアカウントのクライアント作成
        role_arn = aws_config["profile " + dest_prefix]["role_arn"]
        endpoint_url = "https://sts." + dest_region + ".amazonaws.com"
        sts = boto3.client("sts", region_name = dest_region, endpoint_url = endpoint_url)
        cross_account = sts.assume_role(
        RoleArn = role_arn,
        RoleSessionName = "cross_account_" + dest_prefix
        )
        # Credentialsの取得
        cross_access_key = cross_account["Credentials"]["AccessKeyId"]
        cross_secret_key = cross_account["Credentials"]["SecretAccessKey"]
        cross_settion_token = cross_account["Credentials"]["SessionToken"]
        # クロスアカウントでsession取得
        session = Session(
        aws_access_key_id = cross_access_key,
        aws_secret_access_key = cross_secret_key,
        aws_session_token = cross_settion_token,
        region_name = dest_region
        )
        ses = session.client("ses", region_name = dest_region)

        return ses

    # ユーザーリストを取得し、同一ユーザー名が存在しているかチェックする
    def CheckCreateUser(self, client, username):
        marker = None
        returnvalue = False
        while True:
            #ユーザー情報を取得する
            if marker:
                response = client.list_users(MaxItems=50, Marker=marker)
            else:
                response = client.list_users(MaxItems=50)

            for dt1 in response['Users']:
                if dt1['UserName'] == username:
                    returnvalue = True
                    break

            if ('Marker' in response):
                marker = response['Marker']
            else:
                break

        return returnvalue

    # IAMUserを作成する
    def CreateUser(self, client, user):
        response = client.create_user(Path = '/', UserName = user)
        return response

    # ログインプロファイルを作成する
    # required:True(初期パスワード設定要)
    def CreateLoginProfile(self, client, user, password, required):
        response = client.create_login_profile(
            UserName=user,
            Password=password,
            PasswordResetRequired=required
        )
        return response

    #IAMユーザーを指定のグループに属させる
    def AddUserToGroup(self, client, groupName, user):
        response = client.add_user_to_group(GroupName = groupName, UserName = user)
        return response