from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct
import os


class FrontendStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        site_dir: str = "frontend/dist",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        site_dir_abs = os.path.abspath(site_dir)

        site_bucket = s3.Bucket(
            self,
            "SiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
        )

        distribution = cloudfront.Distribution(
            self,
            "SiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(site_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            # If you use client-side routing, uncomment SPA fallback:
            # error_responses=[
            #     cloudfront.ErrorResponse(http_status=403, response_http_status=200, response_page_path="/index.html"),
            #     cloudfront.ErrorResponse(http_status=404, response_http_status=200, response_page_path="/index.html"),
            # ],
        )

        s3deploy.BucketDeployment(
            self,
            "DeployApp",
            destination_bucket=site_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
            sources=[s3deploy.Source.asset(site_dir_abs)],
        )

        CfnOutput(self, "CloudFrontURL", value=f"https://{distribution.domain_name}")
        CfnOutput(self, "SiteBucketName", value=site_bucket.bucket_name)
        CfnOutput(self, "DistributionId", value=distribution.distribution_id)
