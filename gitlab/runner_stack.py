from pathlib import Path

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import core as cdk
from aws_cdk.aws_s3_assets import Asset


class RunnerStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str,
                 gitlab: cdk.Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = cdk.Tags.of(self)
        tags.add(key='Stage', value='DevOps')
        tags.add(key='Module', value='Runner')
        tags.add(key='Owner', value='Vunk.Lai')
        tags.add(key='Name', value='GitLab/Runner', apply_to_launched_instances=True)

        subnets = gitlab.vpc.select_subnets(subnet_group_name='Runner').subnets

        security_group = ec2.SecurityGroup(
            self, 'sg',
            vpc=gitlab.vpc,
            security_group_name='GitLab/Runner:SecurityGroup',
            description='Default Runner Security Group',
            allow_all_outbound=True)

        policy = iam.ManagedPolicy(
            self, 'policy',
            # Use alphanumeric and '+=,.@-_' characters
            managed_policy_name='GitLab-Runner_Policy',
            description='SSM Login',
            statements=[
                iam.PolicyStatement(
                    actions=['ssmmessages:*', 'ssm:UpdateInstanceInformation'],
                    resources=['*']),
            ])

        role = iam.Role(
            self, 'role',
            # Use alphanumeric and '+=,.@-_' characters
            role_name='GitLab-Runner_Role',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            managed_policies=[policy])

        folder = Path(__file__).parent.parent / 'user_data'
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            'apt install unzip',
            'curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "aws_cli_v2.zip"',
            'unzip aws_cli_v2.zip',
            'sudo ./aws/install',
            'aws --version')
        asset = Asset(self, 'asset:userdata', path=str(folder / 'runner.sh'))
        asset.grant_read(role)
        path = user_data.add_s3_download_command(
            bucket=asset.bucket, bucket_key=asset.s3_object_key)
        user_data.add_execute_file_command(
            file_path=path, arguments='--verbose -y')

        template = ec2.LaunchTemplate(
            self, 'template',
            launch_template_name='GitLab/Runner_LaunchTemplate',
            cpu_credits=ec2.CpuCredits.STANDARD,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.lookup(
                name='ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*',
                owners=['099720109477']),
            role=role,
            security_group=security_group,
            user_data=user_data,
            block_devices=[
                ec2.BlockDevice(
                    device_name='/dev/sda1',
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=20,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        delete_on_termination=True,
                    )),
            ]
        )

        ec2.CfnInstance(
            self, 'instance',
            launch_template=ec2.CfnInstance.LaunchTemplateSpecificationProperty(
                version=template.latest_version_number,
                launch_template_id=template.launch_template_id,
            ),
            subnet_id=subnets[0].subnet_id
        )
