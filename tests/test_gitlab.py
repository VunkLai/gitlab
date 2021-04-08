import boto3

session = boto3.Session(profile_name='vj')


def test_vpc():
    ec2 = session.client('ec2')
    response = ec2.describe_vpcs(
        Filter=[{'Name': 'tag:Name', 'Values': ['GitLab/VPC']}])
    VPC = response['Vpcs'][0]

    resource = session.resource('ec2')
    vpc = resource.Vpc(VPC['VpcId'])
    assert vpc.cidr_block == '10.0.0.0/16', f'Invalid CIDR, get {vpc.cidr_block}'
    assert vpc.state == 'avaliable', f'Invalid state, get {vpc.state}'
    assert not vpc.is_default, f'VPC is default, get {vpc.is_default}'
    assert {'Name': 'Stage', 'Value': 'DevOps'} in vpc.tags, f'Invalid tags, get {vpc.tags}'
    assert {'Name': 'Module', 'Value': 'GitLab'} in vpc.tags, f'Invalid tags, get {vpc.tags}'


def test_route53():
    route53 = session.client('route53')


def test_ec2():
    pass
