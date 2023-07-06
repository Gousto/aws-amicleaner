# -*- coding: utf-8 -*-

import json

import boto3
from moto import mock_ec2, mock_autoscaling

from amicleaner.fetch import Fetcher

@mock_ec2
@mock_autoscaling
def test_fetch_zeroed_asg_down_returns_lc_for_scaled_down_asg():
    """ Test fetching of AMIs for autoscaling scaled down """

    # Creating test resources
    ec2 = boto3.client("ec2")
    asg = boto3.client("autoscaling")

    # Create an EC2 launch template
    ec2.create_launch_template(
        LaunchTemplateName="launchtemplate-test1",
        LaunchTemplateData={"ImageId": "ami-28c2b348", "InstanceType": "t2.medium"},
    )

    # Create an Autoscaling group using the launchtemplate with desired set to 0
    asg.create_auto_scaling_group(
        AutoScalingGroupName="autoscaling-test1",
        DesiredCapacity=0,
        MinSize=1,
        MaxSize=1,
        LaunchTemplate={
            "LaunchTemplateName": "launchtemplate-test1",
            "Version": "$Latest",
        },
        AvailabilityZones=["us-west-1a"],
    )

    # Create a launchconfiguration
    asg.create_launch_configuration(
        LaunchConfigurationName="launchconfiguration-test2",
        ImageId="ami-28c2b349",
        InstanceType="t2.medium",
    )

    # Create an Autoscaling group using the launchconfiguration with desired set to 0
    asg.create_auto_scaling_group(
        AutoScalingGroupName="autoscaling-test2",
        DesiredCapacity=0,
        MinSize=1,
        MaxSize=1,
        LaunchConfigurationName="launchconfiguration-test2",
        AvailabilityZones=["us-west-1a"],
    )

    f = Fetcher(ec2=ec2, autoscaling=asg)
    # Testing fetching of AMIs for ASGs scaled down and using LaunchConfig
    amis = f.fetch_zeroed_asg()
    assert amis == ['ami-28c2b349']