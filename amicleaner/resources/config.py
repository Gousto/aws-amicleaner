#!/usr/bin/env python
# -*- coding: utf-8 -*-

# set your aws env vars to production

from blessings import Terminal
import os

os.environ['TERM'] = 'xterm'
# terminal colors
TERM = Terminal()

# Number of previous amis to keep based on grouping strategy
# not including the ami currently running by an ec2 instance
KEEP_PREVIOUS = 4

# Number of days amis to keep based on creation date and grouping strategy
# not including the ami currently running by an ec2 instance
AMI_MIN_DAYS = -1

BOTO3_RETRIES = 10
