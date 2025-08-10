# docstack/ingestion_stack.py
from aws_cdk import (
    Stack,
    Duration,
    BundlingOptions,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class IngestionStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        docs_bucket: s3.IBucket,
        documents_table: dynamodb.ITable,
        nlp_url: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ingestion_fn = _lambda.Function(
            self,
            "IngestionFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.handler",
            # 👇 Bundle requirements.txt + code into /asset-output
            code=_lambda.Code.from_asset(
                "source/lambda/ingestion",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        # Install platform-specific lxml first (without -t)
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: lxml -t /asset-output "
                        # Then install other dependencies
                        "&& pip install -r requirements.txt -t /asset-output "
                        # Copy your Lambda code
                        "&& cp -au . /asset-output",
                    ],
                ),
            ),
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                "DOCUMENTS_TABLE": documents_table.table_name,
                "DOCS_BUCKET": docs_bucket.bucket_name,
                "TEXT_PREFIX": "extracted/",
                "NLP_URL": nlp_url,
            },
        )

        documents_table.grant_read_write_data(ingestion_fn)
        docs_bucket.grant_read(ingestion_fn)
        docs_bucket.grant_put(ingestion_fn)

        rule = events.Rule(
            self,
            "S3ObjectCreatedRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={"bucket": {"name": [docs_bucket.bucket_name]}},
            ),
        )
        rule.add_target(targets.LambdaFunction(ingestion_fn))
