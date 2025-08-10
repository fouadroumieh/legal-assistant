from aws_cdk import (
    Stack,
    CfnOutput,
    aws_apprunner as apprunner,
    aws_ecr_assets as ecr_assets,
    aws_iam as iam,
)
from constructs import Construct
import os


class NlpStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        service_name: str = "docstack-nlp",
        nlp_dir: str = "nlp_service",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        image_asset = ecr_assets.DockerImageAsset(
            self,
            "NlpImage",
            directory=os.path.abspath(nlp_dir),
            platform=ecr_assets.Platform.LINUX_AMD64,  # avoid M1/arm mismatch
        )

        access_role = iam.Role(
            self,
            "NlpAppRunnerAccessRole",
            assumed_by=iam.ServicePrincipal("build.apprunner.amazonaws.com"),
        )
        image_asset.repository.grant_pull(access_role)

        instance_role = iam.Role(
            self,
            "NlpAppRunnerInstanceRole",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
        )
        # (no AWS access needed for NLP itself)

        service = apprunner.CfnService(
            self,
            "NlpService",
            service_name=service_name,
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
                    access_role_arn=access_role.role_arn
                ),
                image_repository=apprunner.CfnService.ImageRepositoryProperty(
                    image_identifier=image_asset.image_uri,
                    image_repository_type="ECR",
                    image_configuration=apprunner.CfnService.ImageConfigurationProperty(
                        port="8080", runtime_environment_variables=[]
                    ),
                ),
                auto_deployments_enabled=True,
            ),
            instance_configuration=apprunner.CfnService.InstanceConfigurationProperty(
                cpu="2 vCPU",  # embeddings + spaCy
                memory="4 GB",
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

        self.service_url = f"https://{service.attr_service_url}"
        CfnOutput(self, "NlpServiceUrl", value=self.service_url)
