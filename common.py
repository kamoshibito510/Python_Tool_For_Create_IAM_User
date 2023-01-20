import boto3
import os
import pyminizip
import secrets
import string
from datetime import datetime, timedelta, timezone

#---------------------------------------------------------
# 定数：
#---------------------------------------------------------
s3 = boto3.resource('s3')

com_aws_console = "https://{aws_account_id}.signin.aws.amazon.com/console"
pptx_file = "AWS_ACCOUNT_USERS_GUIDE.pptx"
zippass = "xxxxxxxx"


class CommonClass:
    # CSVファイル作成と手順書ファイルをアタッチしＺＩＰ化する
    def CsvZipfileComposer(self, user_name, password, bucket):
        # CSV、ZIPファイル作成
        filepath = "/tmp/"
        filename = user_name + ".csv"
        filedata = "User name,Password,Access key ID,Secret access key,Console login link" + "\n"
        filedata = filedata + user_name + "," + password + "," + "" + "," + "" + "," + com_aws_console + "\n"
        csvFilePath = CommonClass.MakeCsvFile(filepath, filename, filedata)
        print("csvFilePath:{}".format(csvFilePath))
        filepath = "/tmp/"
        pptxFilePath = filepath + "\\" + pptx_file
        # 手順書ファイルをS3から取得しtmpフォルダに保存
        s3.meta.client.download_file(bucket, pptx_file, pptxFilePath)
        filelist = []
        filelist.append(csvFilePath)
        filelist.append(pptxFilePath)
        # Zipファイル名を日付入りで作成
        filename = user_name + '_' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S-') + ".zi_"
        zipFilePath = CommonClass.MakeZipMultiFileWithPath(filelist, filepath, filename, zippass)
        # 確認用にS3へZIPファイルを置く
        s3.meta.client.upload_file(zipFilePath, bucket, 'zipfiles_storage/' + filename)

        return zipFilePath

    # 複数ファイルをZIPに圧縮（パスワード付き）
    @staticmethod
    def MakeZipMultiFileWithPath(fileList, filePath, fileName, password):
        if not os.path.exists(filePath):
            os.mkdir(filePath)

        zipFilePath = filePath + "\\" + fileName

        numlist = []
        for i in fileList:
            numlist.append('')

        pyminizip.compress_multiple(fileList, numlist, zipFilePath, password, 5)

        return zipFilePath


    # CSVファイルを作成する
    @staticmethod
    def MakeCsvFile(filePath, fileName, fileData):
        if not os.path.exists(filePath):
            os.mkdir(filePath)

        fileFullPath = filePath + "\\" + fileName
        with open(fileFullPath, "w") as f:
            f.write(fileData)

        return fileFullPath

    # ランダムキーを生成する
    def KeyGenerator(self, size):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        chars += '!@#$%^&*()_+-=[]{}|'

        return ''.join(secrets.choice(chars) for x in range(size))

    # ファイル内のデータを取得して返却する
    @staticmethod
    def GetFileDetail(filepath):
        with open(filepath, mode="r", encoding="utf-8") as f:
            fileData = f.read()
        return fileData