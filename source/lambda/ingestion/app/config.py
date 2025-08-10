
import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ------------------ ENV ------------------
DOCUMENTS_TABLE = os.environ["DOCUMENTS_TABLE"]
DOCS_BUCKET = os.environ["DOCS_BUCKET"]

TEXT_PREFIX = os.environ.get("TEXT_PREFIX", "extracted/")
if not TEXT_PREFIX.endswith("/"):
    TEXT_PREFIX = TEXT_PREFIX + "/"

AWS_REGION = (
    os.environ.get("AWS_REGION")
    or os.environ.get("AWS_DEFAULT_REGION")
    or "eu-central-1"
)

NLP_URL = os.environ.get("NLP_URL")  # e.g. https://<id>.<region>.awsapprunner.com
if NLP_URL and not NLP_URL.startswith(("http://", "https://")):
    NLP_URL = "https://" + NLP_URL

# ---------------- AWS CLIENTS ------------
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
doc_table = dynamodb.Table(DOCUMENTS_TABLE)
s3 = boto3.client("s3", region_name=AWS_REGION)
