#!/usr/bin/env python3
import os
import aws_cdk as cdk

from cdk.core_stack import CoreStack
from cdk.ingestion_stack import IngestionStack
from cdk.frontend_stack import FrontendStack
from cdk.api_stack import ApiStack
from cdk.nlp_stack import NlpStack

app = cdk.App()

# stage support (defaults to dev)
stage = (app.node.try_get_context("stage") or os.getenv("STAGE") or "dev").lower()
project = "docstack"
account = os.getenv("CDK_DEFAULT_ACCOUNT")
region = os.getenv("CDK_DEFAULT_REGION") or "us-east-1"
env = cdk.Environment(account=account, region=region)


def name(suffix: str) -> str:
    return f"{project}-{stage}-{suffix}"


core = CoreStack(app, "CoreStack", env=env, stack_name=name("core"))

nlp = NlpStack(
    app,
    "NlpStack",
    env=env,
    stack_name=name("nlp"),
    service_name=f"{project}-{stage}-nlp",
    nlp_dir="nlp_service",
)

ing = IngestionStack(
    app,
    "IngestionStack",
    env=env,
    stack_name=name("ingestion"),
    docs_bucket=core.docs_bucket,
    documents_table=core.documents_table,
    nlp_url=nlp.service_url,
)

api = ApiStack(
    app,
    "ApiStack",
    env=env,
    stack_name=name("docapi"),
    documents_table=core.documents_table,
    docs_bucket=core.docs_bucket,
    service_name=f"{project}-{stage}-docapi",
    docapi_dir="docapi",
    nlp_url=nlp.service_url,
)

fe = FrontendStack(
    app,
    "FrontendStack",
    env=env,
    stack_name=name("frontend"),
)

# Optional tagging
for st in (core, ing, api, fe):
    cdk.Tags.of(st).add("Project", project)
    cdk.Tags.of(st).add("Stage", stage)

app.synth()
