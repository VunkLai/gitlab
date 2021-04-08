from pathlib import Path

import requests
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_route53 as route53
from aws_cdk import core as cdk
from aws_cdk.aws_s3_assets import Asset

DOMAIN = ''


class GitlabStack(cdk.Stack):

    @property
    def home_ip(self):
        response = requests.get('http://checkip.amazonaws.com/')
        assert response.status_code == requests.codes.ok, response.text
        return response.text.strip() + '/32'

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = cdk.Tags.of(self)
        tags.add(key='Stage', value='DevOps')
        tags.add(key='Module', value='GitLab')
        tags.add(key='Owner', value='Vunk.Lai')
        tags.add(key='Name', value='GitLab/GitLab', apply_to_launched_instances=True)

        vpc = ec2.Vpc(
            self, 'vpc',
            max_azs=1,
            cidr=ec2.Vpc.DEFAULT_CIDR_RANGE,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name='Generic',
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                    reserved=True),
                ec2.SubnetConfiguration(
                    name='GitLab',
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24),
                ec2.SubnetConfiguration(
                    name='Runner',
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24),
            ])
        cdk.Tags.of(vpc).add(key='Name', value='GitLab/VPC')

        subnets = vpc.select_subnets(subnet_group_name='GitLab').subnets

        security_group = ec2.SecurityGroup(
            self, 'sg',
            vpc=vpc,
            security_group_name='GitLab/GitLab:SecurityGroup',
            description='Default GitLab Security Group',
            allow_all_outbound=True)
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), 'LetsEncrypt HTTP-01')
        security_group.add_ingress_rule(
            ec2.Peer.ipv4(self.home_ip), ec2.Port.tcp(443), 'Home')
        security_group.add_ingress_rule(
            ec2.Peer.ipv4(ec2.Vpc.DEFAULT_CIDR_RANGE), ec2.Port.tcp(443), 'LAN')

        policy = iam.ManagedPolicy(
            self, 'policy',
            # Use alphanumeric and '+=,.@-_' characters
            managed_policy_name='GitLab-GitLab_Policy',
            description='SSM Login',
            statements=[
                iam.PolicyStatement(
                    actions=['ssmmessages:*', 'ssm:UpdateInstanceInformation'],
                    resources=['*']),
            ])

        role = iam.Role(
            self, 'role',
            # Use alphanumeric and '+=,.@-_' characters
            role_name='GitLab-GitLab_Role',
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
        asset = Asset(self, 'asset:gitlab.rb', path=str(folder / 'gitlab.rb'))
        asset.grant_read(role)
        user_data.add_s3_download_command(
            bucket=asset.bucket, bucket_key=asset.s3_object_key,
            local_file='/etc/gitlab/gitlab.rb')
        asset = Asset(self, 'asset:userdata', path=str(folder / 'gitlab.sh'))
        asset.grant_read(role)
        path = user_data.add_s3_download_command(
            bucket=asset.bucket, bucket_key=asset.s3_object_key)
        user_data.add_execute_file_command(
            file_path=path, arguments='--verbose -y')
        # asset = Asset(
        #     self, 'asset:prometheus:rules', path=str(folder / 'gitlab.rules.json'))

        template = ec2.LaunchTemplate(
            self, 'template',
            # Use alphanumeric and '-()./_' characters
            launch_template_name='GitLab/GitLab_LaunchTemplate',
            cpu_credits=ec2.CpuCredits.STANDARD,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM),
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
                        volume_size=8,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        delete_on_termination=True,
                    )),
                ec2.BlockDevice(
                    device_name='/dev/sdf',
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=20,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        delete_on_termination=False,
                    ))
            ]
        )

        instance = ec2.CfnInstance(
            self, 'instance',
            launch_template=ec2.CfnInstance.LaunchTemplateSpecificationProperty(
                version=template.latest_version_number,
                launch_template_id=template.launch_template_id,
            ),
            subnet_id=subnets[0].subnet_id
        )

        zone = route53.HostedZone.from_lookup(
            self, 'zone', domain_name=DOMAIN)
        route53.CnameRecord(
            self, 'cname',
            record_name='gitlab',
            domain_name=instance.attr_public_dns_name,
            zone=zone,
            ttl=cdk.Duration.minutes(5))

        self.vpc = vpc
        self.security_group = security_group
