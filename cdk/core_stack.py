from typing import Optional
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class CoreStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Enable EventBridge so S3 object-created events go to the default event bus
        self.docs_bucket = s3.Bucket(
            self,
            "DocsBucket",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            event_bridge_enabled=True,
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.GET,
                        s3.HttpMethods.HEAD,
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    exposed_headers=["ETag"],
                )
            ],
        )

        self.documents_table = dynamodb.Table(
            self,
            "DocumentsTable",
            partition_key=dynamodb.Attribute(
                name="documentId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        CfnOutput(self, "DocsBucketName", value=self.docs_bucket.bucket_name)
        CfnOutput(self, "DocumentsTableName", value=self.documents_table.table_name)
