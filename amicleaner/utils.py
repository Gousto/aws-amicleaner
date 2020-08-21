#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from builtins import object
import argparse

from prettytable import PrettyTable

from .resources.config import KEEP_PREVIOUS, AMI_MIN_DAYS


class Printer(object):

    """ Pretty table prints methods """
    @staticmethod
    def print_report(candidates):

        """ Print AMI collection results """

        if not candidates:
            return

        eligible_amis_table = PrettyTable(
            ["AMI ID", "AMI Name", "Creation Date"]
        )
        for ami in candidates:
            eligible_amis_table.add_row([
                ami.id,
                ami.name,
                ami.creation_date
            ])
        print("\nAMIs to be removed:")
        print(eligible_amis_table.get_string(sortby="AMI Name"), "\n\n")

    @staticmethod
    def print_failed_snapshots(snapshots):

        snap_table = PrettyTable(["Failed Snapshots"])

        for snap in snapshots:
            snap_table.add_row([snap])
        print(snap_table)

    @staticmethod
    def print_orphan_snapshots(snapshots):

        snap_table = PrettyTable(["Orphan Snapshots"])

        for snap in snapshots:
            snap_table.add_row([snap])
        print(snap_table)


def parse_args(args):
    parser = argparse.ArgumentParser(description='Clean your AMIs on your '
                                                 'AWS account. Your AWS '
                                                 'credentials must be sourced')

    parser.add_argument("-v", "--version",
                        dest='version',
                        action="store_true",
                        help="Prints version and exits")

    parser.add_argument("--from-ids",
                        dest='from_ids',
                        nargs='+',
                        help="AMI id(s) you simply want to remove")

    parser.add_argument("--name",
                        dest='filter_names',
                        nargs='+',
                        help="Names to filter the AMIs on (match ANY name substring): values")

    parser.add_argument("--tag",
                        dest='filter_tags',
                        action="append",
                        help="Tags to filter the AMIs on (match ALL tags exactly): tag=value")

    parser.add_argument("--full-report",
                        action="store_true",
                        help="Deprecated (Does nothing)")

    parser.add_argument("--mapping-key",
                        dest='mapping_key',
                        help="Deprecated, use --name option instead. Valid option: name")

    parser.add_argument("--mapping-values",
                        dest='mapping_values',
                        nargs='+',
                        help="Deprecated, use --name option instead")

    parser.add_argument("--exclude-ami",
                        dest='exclude_amis',
                        nargs='+',
                        help="List of AMI IDs to be excluded")

    parser.add_argument("--keep-previous",
                        dest='keep_previous',
                        type=int,
                        default=KEEP_PREVIOUS,
                        help="Number of previous AMI to keep excluding those "
                             "currently being running")

    parser.add_argument("-f", "--force-delete",
                        dest='force_delete',
                        action="store_true",
                        help="Skip confirmation")

    parser.add_argument("--check-orphans",
                        dest='check_orphans',
                        action="store_true",
                        help="Check and clean orphaned snapshots")

    parser.add_argument("--ami-min-days",
                        dest='ami_min_days',
                        type=int,
                        default=AMI_MIN_DAYS,
                        help="Number of days AMI to keep excluding those "
                             "currently being running")

    parsed_args = parser.parse_args(args)
    if parsed_args.mapping_key and not parsed_args.mapping_values:
        print("missing mapping-values\n")
        parser.print_help()
        return None

    return parsed_args
