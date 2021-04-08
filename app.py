#!/usr/bin/env python3

import os

from aws_cdk import core as cdk

from gitlab import GitlabStack, RunnerStack

app = cdk.App()
env = cdk.Environment(
    account=os.environ['CDK_DEFAULT_ACCOUNT'],
    region=os.environ['CDK_DEFAULT_REGION'])

gitlab = GitlabStack(app, "GitlabStack", env=env)
runner = RunnerStack(app, "RunnerStack", env=env, gitlab=gitlab)
runner.add_dependency(gitlab)

app.synth()
