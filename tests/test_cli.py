# -*- coding: utf-8 -*-

import json

import boto3
from moto import mock_ec2, mock_autoscaling
from datetime import datetime

from amicleaner.cli import App
from amicleaner.fetch import Fetcher
from amicleaner.utils import parse_args, Printer
from amicleaner.resources.models import AMI, AWSEC2Instance, AWSTag


@mock_ec2
@mock_autoscaling
def test_fetch_and_prepare():
    parser = parse_args(['--keep-previous', '0'])
    assert App(parser).prepare_candidates() is None


@mock_ec2
@mock_autoscaling
def test_deletion():
    """ Test deletion methods """

    base_ami = "ami-1234abcd"

    parser = parse_args(
        [
            '--keep-previous', '0',
            '--mapping-key', 'name',
            '--mapping-values', 'test-ami']
    )

    ec2 = boto3.client('ec2')
    reservation = ec2.run_instances(
        ImageId=base_ami, MinCount=1, MaxCount=1
    )
    instance = reservation["Instances"][0]

    # create amis
    images = []
    for i in range(5):
        image = ec2.create_image(
            InstanceId=instance.get("InstanceId"),
            Name="test-ami"
        )
        images.append(image.get("ImageId"))

    # delete one AMI by id
    app = App(parser)
    asg = boto3.client('autoscaling')
    f = Fetcher(ec2=ec2, autoscaling=asg)

    assert len(f.fetch_available_amis()) == 5
    assert app.prepare_delete_amis(
        candidates=[images[4]], from_ids=True
    ) is None
    assert len(f.fetch_available_amis()) == 4

    # delete with mapping strategy
    candidates = app.prepare_candidates()
    assert len(candidates) == 4
    assert app.prepare_delete_amis(candidates) is None
    assert len(f.fetch_available_amis()) == 0


@mock_ec2
@mock_autoscaling
def test_deletion_ami_min_days():
    """ Test deletion methods """

    # creating tests objects
    first_ami = AMI()
    first_ami.name = "test-ami"
    first_ami.id = 'ami-28c2b348'
    first_ami.creation_date = "2017-11-04T01:35:31.000Z"

    second_ami = AMI()
    second_ami.name = "test-ami"
    second_ami.id = 'ami-28c2b349'
    second_ami.creation_date = "2017-11-04T01:35:31.000Z"

    # constructing dicts
    amis_dict = dict()
    amis_dict[first_ami.id] = first_ami
    amis_dict[second_ami.id] = second_ami

    parser = parse_args(
        [
            '--keep-previous', '0',
            '--ami-min-days', '1',
            '--mapping-key', 'name',
            '--mapping-values', 'test-ami']
    )

    app = App(parser)
    # testing filter
    candidates = app.fetch_candidates(amis_dict)

    candidates_tobedeleted = app.prepare_candidates(candidates)
    assert len(candidates) == 2
    assert len(candidates_tobedeleted) == 2

    parser = parse_args(
        [
            '--keep-previous', '0',
            '--ami-min-days', '10000',
            '--mapping-key', 'name',
            '--mapping-values', 'test-ami']
    )

    app = App(parser)
    candidates_tobedeleted2 = app.prepare_candidates(candidates)
    assert len(candidates) == 2
    assert len(candidates_tobedeleted2) == 0


@mock_ec2
@mock_autoscaling
def test_deletion_filtered_name():
    """ Test deletion methods """

    # creating tests objects
    first_ami = AMI()
    first_ami.name = "test-ami-delete-1"
    first_ami.id = 'ami-28c2b348'
    first_ami.creation_date = "2017-11-04T01:35:31.000Z"

    second_ami = AMI()
    second_ami.name = "test-ami-keepme"
    second_ami.id = 'ami-28c2b349'
    second_ami.creation_date = "2017-11-04T01:35:31.000Z"

    third_ami = AMI()
    third_ami.name = "test-ami-delete-2"
    third_ami.id = 'ami-28c2b350'
    third_ami.creation_date = "2017-11-04T01:35:31.000Z"

    # constructing dicts
    amis_dict = dict()
    amis_dict[first_ami.id] = first_ami
    amis_dict[second_ami.id] = second_ami
    amis_dict[third_ami.id] = third_ami

    parser = parse_args(
        [
            '--keep-previous', '0',
            '--mapping-key', 'name',
            '--mapping-values', 'test-ami-delete']
    )

    app = App(parser)
    # testing filter
    candidates = app.fetch_candidates(amis_dict)

    candidates_tobedeleted = app.prepare_candidates(candidates)
    assert len(candidates) == 3
    assert candidates_tobedeleted == [first_ami, third_ami]

    parser = parse_args(
        [
            '--keep-previous', '0',
            '--name', 'test-ami-delete-1',
        ]
    )

    app = App(parser)
    candidates_tobedeleted2 = app.prepare_candidates(candidates)
    assert len(candidates) == 3
    assert candidates_tobedeleted2 == [first_ami]


@mock_ec2
@mock_autoscaling
def test_deletion_filtered_tags():
    """ Test deletion methods """

    # creating tests objects
    first_ami = AMI()
    first_ami.name = "test-ami1"
    first_ami.id = 'ami-28c2b348'
    first_ami.creation_date = "2017-11-04T01:35:31.000Z"

    second_ami = AMI()
    second_ami.name = "test-ami2"
    second_ami.id = 'ami-28c2b349'
    second_ami.creation_date = "2017-11-04T01:35:31.000Z"
    second_ami.tags = [
        AWSTag.object_with_json(dict(Key="env", Value="prod")),
        AWSTag.object_with_json(dict(Key="role", Value="nginx")),
    ]

    third_ami = AMI()
    third_ami.name = "test-ami3"
    third_ami.id = 'ami-28c2b350'
    third_ami.creation_date = "2017-11-04T01:35:31.000Z"
    third_ami.tags = [
        AWSTag.object_with_json(dict(Key="env", Value="dev")),
        AWSTag.object_with_json(dict(Key="role", Value="nginx")),
    ]

    # constructing dicts
    amis_dict = dict()
    amis_dict[first_ami.id] = first_ami
    amis_dict[second_ami.id] = second_ami
    amis_dict[third_ami.id] = third_ami

    parser = parse_args(
        [
            '--keep-previous', '0',
            '--tag', 'role=nginx',
        ]
    )

    app = App(parser)
    # testing filter
    candidates = app.fetch_candidates(amis_dict)

    candidates_tobedeleted = app.prepare_candidates(candidates)
    assert len(candidates) == 3
    assert candidates_tobedeleted == [second_ami, third_ami]

    parser = parse_args(
        [
            '--keep-previous', '0',
            '--tag', 'role=nginx',
            '--tag', 'env=dev',
        ]
    )

    app = App(parser)
    candidates_tobedeleted2 = app.prepare_candidates(candidates)
    assert len(candidates) == 3
    assert candidates_tobedeleted2 == [third_ami]


def test_fetch_candidates():
    # creating tests objects
    first_ami = AMI()
    first_ami.id = 'ami-28c2b348'
    first_ami.creation_date = datetime.now()

    first_instance = AWSEC2Instance()
    first_instance.id = 'i-9f9f6a2a'
    first_instance.name = "first-instance"
    first_instance.image_id = first_ami.id
    first_instance.launch_time = datetime.now()

    second_ami = AMI()
    second_ami.id = 'unused-ami'
    second_ami.creation_date = datetime.now()

    second_instance = AWSEC2Instance()
    second_instance.id = 'i-9f9f6a2b'
    second_instance.name = "second-instance"
    second_instance.image_id = first_ami.id
    second_instance.launch_time = datetime.now()

    # constructing dicts
    amis_dict = dict()
    amis_dict[first_ami.id] = first_ami
    amis_dict[second_ami.id] = second_ami

    instances_dict = dict()
    instances_dict[first_instance.image_id] = instances_dict
    instances_dict[second_instance.image_id] = second_instance

    # testing filter
    unused_ami_dict = App(parse_args([])).fetch_candidates(
        amis_dict, list(instances_dict)
    )
    assert len(unused_ami_dict) == 1
    assert second_ami in unused_ami_dict


def test_fetch_candidates_exclude_amis():
    # creating tests objects
    first_ami = AMI()
    first_ami.id = 'ami-28c2b348'
    first_ami.creation_date = datetime.now()

    first_instance = AWSEC2Instance()
    first_instance.id = 'i-9f9f6a2a'
    first_instance.name = "first-instance"
    first_instance.image_id = first_ami.id
    first_instance.launch_time = datetime.now()

    second_ami = AMI()
    second_ami.id = 'excluded-ami'
    second_ami.creation_date = datetime.now()

    second_instance = AWSEC2Instance()
    second_instance.id = 'i-9f9f6a2b'
    second_instance.name = "second-instance"
    second_instance.image_id = first_ami.id
    second_instance.launch_time = datetime.now()

    # constructing dicts
    amis_dict = dict()
    amis_dict[first_ami.id] = first_ami
    amis_dict[second_ami.id] = second_ami

    instances_dict = dict()
    instances_dict[first_instance.image_id] = instances_dict
    instances_dict[second_instance.image_id] = second_instance

    # testing filter
    unused_ami_dict = App(parse_args(["--exclude-ami", "excluded-ami"])).fetch_candidates(
        amis_dict, list(instances_dict)
    )
    assert len(unused_ami_dict) == 0


def test_fetch_candidates():
    # creating tests objects
    first_ami = AMI()
    first_ami.id = 'ami-28c2b348'
    first_ami.creation_date = datetime.now()

    first_instance = AWSEC2Instance()
    first_instance.id = 'i-9f9f6a2a'
    first_instance.name = "first-instance"
    first_instance.image_id = first_ami.id
    first_instance.launch_time = datetime.now()

    second_ami = AMI()
    second_ami.id = 'unused-ami'
    second_ami.creation_date = datetime.now()

    second_instance = AWSEC2Instance()
    second_instance.id = 'i-9f9f6a2b'
    second_instance.name = "second-instance"
    second_instance.image_id = first_ami.id
    second_instance.launch_time = datetime.now()

    # constructing dicts
    amis_dict = dict()
    amis_dict[first_ami.id] = first_ami
    amis_dict[second_ami.id] = second_ami

    instances_dict = dict()
    instances_dict[first_instance.image_id] = instances_dict
    instances_dict[second_instance.image_id] = second_instance

    # testing filter
    unused_ami_dict = App(parse_args([])).fetch_candidates(
        amis_dict, list(instances_dict)
    )
    assert len(unused_ami_dict) == 1
    assert second_ami in unused_ami_dict


def test_parse_args_no_args():
    parser = parse_args([])
    assert parser.force_delete is False
    assert parser.from_ids is None
    assert parser.from_ids is None
    assert parser.full_report is False
    assert parser.mapping_key is None
    assert parser.mapping_values is None
    assert parser.keep_previous is 4
    assert parser.ami_min_days is -1


def test_parse_args():
    parser = parse_args(['--keep-previous', '10', '--full-report'])
    assert parser.keep_previous == 10
    assert parser.full_report is True

    parser = parse_args(['--mapping-key', 'name'])
    assert parser is None

    parser = parse_args(['--mapping-key', 'name', '--mapping-values', 'foo'])
    assert parser.mapping_key == "name"
    assert len(parser.mapping_values) == 1

    parser = parse_args(['--ami-min-days', '10'])
    assert parser.ami_min_days == 10

    parser = parse_args(['--name', 'foo'])
    assert parser.filter_names == ["foo"]

    parser = parse_args(['--name', 'foo', 'bar'])
    assert parser.filter_names == ["foo", 'bar']

    parser = parse_args(['--tag', 'foo=alpha', '--tag', 'bar=beta'])
    assert parser.filter_tags == ["foo=alpha", "bar=beta"]

    parser = parse_args(['--exclude-ami', 'foo', 'bar'])
    assert parser.exclude_amis == ["foo", "bar"]


def test_print_report():
    assert Printer.print_report({}) is None

    with open("tests/mocks/ami.json") as mock_file:
        json_to_parse = json.load(mock_file)
        ami = AMI.object_with_json(json_to_parse)
        candidates = [ami]
        assert Printer.print_report(candidates) is None


def test_print_failed_snapshots():
    assert Printer.print_failed_snapshots({}) is None
    assert Printer.print_failed_snapshots(["ami-one", "ami-two"]) is None


def test_print_orphan_snapshots():
    assert Printer.print_orphan_snapshots({}) is None
    assert Printer.print_orphan_snapshots(["ami-one", "ami-two"]) is None


def test_print_defaults():
    assert App(parse_args([])).print_defaults() is None
