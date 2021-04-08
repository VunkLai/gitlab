import boto3


class Instances:

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

    def stop(self):
        client = self.session.client('ec2')
        client.stop_instances(InstanceIds=list(self.ids))


def main():
    instances = Instances()
    assert len(instances.instances) == 2, f'instances: {instances.ids}'
    instances.stop()


if __name__ == '__main__':
    main()
