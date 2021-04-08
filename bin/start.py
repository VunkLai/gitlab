import time

import boto3


class Instances:

    _gitlab = None

    def __init__(self):
        self.session = boto3.Session(profile_name='vj')
        self.instances = list(self.load())

    def load(self):
        client = self.session.client('ec2')
        response = client.describe_instances(
            Filters=[{'Name': 'tag:Stage', 'Values': ['DevOps']}])
        resource = self.session.resource('ec2')
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                yield resource.Instance(instance['InstanceId'])

    @property
    def ids(self):
        for instance in self.instances:
            yield instance.id

    @property
    def gitlab(self):
        if self._gtilab is None:
            for instance in self.instances:
                if {'Name': 'Module', 'Value': 'GitLab'} in instance.tags:
                    self._gitlab = instance
        return self._gitlab

    def start(self):
        client = self.session.client('ec2')
        client.start_instances(InstanceIds=list(self.ids))

    def update_dns_record(self):
        while True:
            time.sleep(10)
            self.gitlab.reload()
            if self.gitlab.state['Name'] == 'running':
                hosted_zone = HostedZone(session=self.session)
                hosted_zone.update_record('gitlab', self.gitlab.public_dns_name)
                break


class HostedZone:

    domain = '.vj-workshop.com'

    def __init__(self, session):
        self.session = session
        self.hosted_zone = self.load()

    def load(self):
        client = self.session.client('route53')
        response = client.list_hosted_zones()
        return response['HostedZones'][0]

    @property
    def id(self):
        return self.hosted_zone['Id']

    def update_record(self, name: str, public_dns_name: str):
        record = {
            'Action': 'UPSERT',
            'ResourceRecordSet': {
                'Name': name + self.domain,
                'Type': 'CNAME',
                'TTL': 3600,
                'ResourceRecords': [{'Value': public_dns_name}]
            }
        }
        client = self.session.client('route53')
        client.change_resource_record_sets(
            HostedZoneId=self.id, ChangeBatch={'Changes': [record]})


def main():
    instances = Instances()
    assert len(instances.ids) == 2, f'Instances: get {instances.ids}'
    instances.start()
    instances.update_dns_record()


if __name__ == '__main__':
    main()
