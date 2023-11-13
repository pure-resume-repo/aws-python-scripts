import json
import subprocess
import sys

# this script will automatically place new MFA credentials into AWS credentials file. If you have
# your setup like this you should have no problems using it:
# usage: python3 set_daily_aws_credentials.py 123456

# getting/sending commandline arguments
new_token = sys.argv[1]
bashCommand = (
    "aws sts get-session-token --serial-number arn:aws:iam::123456:mfa/first.lastname --token-code "
    + new_token
    + " --profile original"
)
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()

# formatting response and saving in variables
new_credentials = output.decode("utf-8").replace("\\n", "")
new_credentials = json.loads(new_credentials)
aws_access_key_id = new_credentials["Credentials"]["AccessKeyId"]
aws_secret_access_key = new_credentials["Credentials"]["SecretAccessKey"]
aws_session_token = new_credentials["Credentials"]["SessionToken"]

# putting everything in the aws credentials file
original_creds = "[original]\naws_access_key_id = your_orinial_id_key\naws_secret_access_key = your_original_secret_key\n\n"
default_creds = (
    "[default]\naws_access_key_id = "
    + aws_access_key_id
    + "\naws_secret_access_key = "
    + aws_secret_access_key
    + "\naws_session_token = "
    + aws_session_token
)
f = open("/home/username/.aws/credentials", "w")
f.write(original_creds + default_creds)
f.close()
