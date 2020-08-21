# -*- coding: utf-8 -*-

from datetime import datetime
from moto import mock_ec2

from amicleaner.core import AMICleaner, OrphanSnapshotCleaner
from amicleaner.resources.models import AMI, AWSTag, AWSBlockDevice


def test_reduce_without_rotation_number():
    # creating tests objects
    first_ami = AMI()
    first_ami.id = 'ami-28c2b348'
    first_ami.name = "ubuntu-20160102"
    first_ami.creation_date = datetime(2016, 1, 10)

    # just prod
    second_ami = AMI()
    second_ami.id = 'ami-28c2b349'
    second_ami.name = "ubuntu-20160103"
    second_ami.creation_date = datetime(2016, 1, 11)

    # prod and web-server
    third_ami = AMI()
    third_ami.id = 'ami-28c2b350'
    third_ami.name = "debian-20160104"
    third_ami.creation_date = datetime(2016, 1, 12)

    # creating amis to drop dict
    candidates = [second_ami, third_ami, first_ami]

    assert AMICleaner().reduce_candidates(candidates) == candidates


def test_reduce_without_snapshot_id():
    # creating block device
    first_block_device = AWSBlockDevice()
    first_block_device.snapshot_id = None

    # creating tests objects
    first_ami = AMI()
    first_ami.id = 'ami-28c2b348'
    first_ami.name = "ubuntu-20160102"
    first_ami.block_device_mappings.append(first_block_device)

    # creating amis to drop dict
    candidates = [first_ami]

    assert AMICleaner().reduce_candidates(candidates) == candidates


def test_reduce():
    # creating tests objects
    first_ami = AMI()
    first_ami.id = 'ami-28c2b348'
    first_ami.name = "ubuntu-20160102"
    first_ami.creation_date = datetime(2016, 1, 10)

    # just prod
    second_ami = AMI()
    second_ami.id = 'ami-28c2b349'
    second_ami.name = "ubuntu-20160103"
    second_ami.creation_date = datetime(2016, 1, 11)

    # prod and web-server
    third_ami = AMI()
    third_ami.id = 'ami-28c2b350'
    third_ami.name = "debian-20160104"
    third_ami.creation_date = datetime(2016, 1, 12)

    # keep 2 recent amis
    candidates = [second_ami, third_ami, first_ami]
    rotation_number = 2
    cleaner = AMICleaner()
    left = cleaner.reduce_candidates(candidates, rotation_number)
    assert len(left) == 1
    assert left[0].id == first_ami.id

    # keep 1 recent ami
    rotation_number = 1
    left = cleaner.reduce_candidates(candidates, rotation_number)
    assert len(left) == 2
    assert left[0].id == second_ami.id

    # keep 5 recent amis
    rotation_number = 5
    left = cleaner.reduce_candidates(candidates, rotation_number)
    assert len(left) == 0


def test_remove_ami_from_none():
    assert AMICleaner().remove_amis(None) == []


@mock_ec2
def test_fetch_snapshots_from_none():

    cleaner = OrphanSnapshotCleaner()

    assert len(cleaner.get_snapshots_filter()) > 0
    assert type(cleaner.fetch()) is list
    assert len(cleaner.fetch()) == 0


"""
@mock_ec2
def test_fetch_snapshots():
    base_ami = "ami-1234abcd"

    conn = boto3.client('ec2')
    reservation = conn.run_instances(
        ImageId=base_ami, MinCount=1, MaxCount=1
    )
    instance = reservation["Instances"][0]

    # create amis
    images = []
    for i in xrange(5):
        image = conn.create_image(
            InstanceId=instance.get("InstanceId"),
            Name="test-ami"
        )
        images.append(image.get("ImageId"))

    # deleting two amis, creating orphan snpashots condition
    conn.deregister_image(ImageId=images[0])
    conn.deregister_image(ImageId=images[1])

    cleaner = OrphanSnapshotCleaner()
    assert len(cleaner.fetch()) == 0
"""
