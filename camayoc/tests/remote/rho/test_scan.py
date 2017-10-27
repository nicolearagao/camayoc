# coding=utf-8
"""Tests for ``rho scan`` commands.

These tests are parametrized on the profiles listed in the config file. If scan
is successful, all facts will be validated before test fails, and then all
failed facts will be reported with associated host.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Rho
:testtype: functional
:upstream: yes
"""

import csv
import os
import pexpect
import pytest
import unittest
from io import BytesIO

from camayoc import config
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.tests.rho.utils import auth_add, input_vault_password


def profiles():
    """Gather profiles from config file."""
    try:
        profs = config.get_config()['rho']['profiles']
    except ConfigFileNotFoundError:
        profs = []
    return profs

# The test will execute once per profile.
@pytest.mark.parametrize(
    'profile', profiles(),
    ids=[p['name'] for p in profiles()]
    )
def test_scan(isolated_filesystem, profile):
    """Scan the machines listed in profile.

    :id: 6ee18084-86db-45ea-8fdd-59fed5639170
    :description: Scan a profile
    :steps:
            1) Run ``rho scan --profile <profile> --reportfile <reportfile>``
    :expectedresults:
        A scan is performed and a report is generated
    """
    cfg = config.get_config()

    for auth in cfg['rho']['auths']:
        auth_add({
            'name': auth['name'],
            'username': auth['username'],
            'sshkeyfile': auth['sshkeyfile'],
        })

    auths = ' '.join(item for item in profile['auths'])
    hosts = ' '.join(item for item in profile['hosts'])
    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(profile['name'], auths, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect(
        'Profile "{}" was added'.format(profile['name'])) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    reportfile = '{}-report.csv'.format(profile['name'])
    rho_scan = pexpect.spawn(
        'rho scan --profile {} --reportfile {} --facts all'
        .format(profile['name'], reportfile),
        timeout=300,
    )
    input_vault_password(rho_scan)
    rho_scan.logfile = BytesIO()
    assert rho_scan.expect(pexpect.EOF) == 0
    logfile = rho_scan.logfile.getvalue().decode('utf-8')
    rho_scan.logfile.close()
    rho_scan.close()
    assert rho_scan.exitstatus == 0, logfile
    assert os.path.isfile(reportfile)

@pytest.mark.facts_needed
@pytest.mark.parametrize('fact', profiles())
def test_facts(fact):
    assert fact['expected'] == fact['actual']
