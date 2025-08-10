from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_apprunner as apprunner,
    aws_ecr_assets as ecr_assets,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct
import os


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        documents_table: dynamodb.ITable,
        docs_bucket: s3.IBucket,
        nlp_url: str,
        service_name: str = "docstack-docapi",
        docapi_dir: str = "docapi",  # local path with Dockerfile + app
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1) Build and upload Docker image to ECR as linux/amd64 (fixes M1/M2 "exec format error")
        image_asset = ecr_assets.DockerImageAsset(
            self,
            "DocApiImage",
            directory=os.path.abspath(docapi_dir),
            platform=ecr_assets.Platform.LINUX_AMD64,  # force amd64
        )

        # 2) Role App Runner uses to pull from ECR
        access_role = iam.Role(
            self,
            "AppRunnerAccessRole",
            assumed_by=iam.ServicePrincipal("build.apprunner.amazonaws.com"),
        )
        image_asset.repository.grant_pull(access_role)

        # 3) Instance role for the running service
        instance_role = iam.Role(
            self,
            "AppRunnerInstanceRole",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
        )
        documents_table.grant_read_write_data(instance_role)
        docs_bucket.grant_put(instance_role)
        docs_bucket.grant_read(instance_role)  # optional (only if you GET objects)

        # 4) App Runner service from the ECR image
        service = apprunner.CfnService(
            self,
            "DocApiService",
            service_name=service_name,
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
                    access_role_arn=access_role.role_arn
                ),
                image_repository=apprunner.CfnService.ImageRepositoryProperty(
                    image_identifier=image_asset.image_uri,
                    image_repository_type="ECR",
                    image_configuration=apprunner.CfnService.ImageConfigurationProperty(
                        port="8080",
                        runtime_environment_variables=[
                            # Dynamo / S3 names
                            apprunner.CfnService.KeyValuePairProperty(
                                name="DOCUMENTS_TABLE", value=documents_table.table_name
                            ),
                            apprunner.CfnService.KeyValuePairProperty(
                                name="DOCS_BUCKET", value=docs_bucket.bucket_name
                            ),
                            apprunner.CfnService.KeyValuePairProperty(
                                name="NLP_URL", value=nlp_url
                            ),
                            # Region hints so the app can presign with the **regional** endpoint
                            apprunner.CfnService.KeyValuePairProperty(
                                name="AWS_REGION", value=self.region
                            ),
                            apprunner.CfnService.KeyValuePairProperty(
                                name="AWS_DEFAULT_REGION", value=self.region
                            ),
                            apprunner.CfnService.KeyValuePairProperty(
                                name="DOCS_BUCKET_REGION", value=self.region
                            ),
                        ],
                    ),
                ),
                auto_deployments_enabled=True,
            ),
            instance_configuration=apprunner.CfnService.InstanceConfigurationProperty(
                cpu="1 vCPU",
                memory="2 GB",
                instance_role_arn=instance_role.role_arn,
            ),
            health_check_configuration=apprunner.CfnService.HealthCheckConfigurationProperty(
                protocol="HTTP",
                path="/health",
                interval=10,
                timeout=5,
                healthy_threshold=1,
                unhealthy_threshold=3,
            ),
        )

        CfnOutput(self, "DocApiServiceUrl", value=service.attr_service_url)
