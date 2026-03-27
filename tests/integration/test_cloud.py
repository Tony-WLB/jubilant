from __future__ import annotations

import contextlib
import uuid
from collections.abc import Mapping
from typing import Any

import pytest

import jubilant

UNSUPPORTED_TOKENS = (
    'unknown command',
    'unrecognized command',
    'not implemented',
    'permission denied',
)


def _skip_if_unsupported(exc: jubilant.CLIError) -> None:
    message = str(exc).lower()
    if any(token in message for token in UNSUPPORTED_TOKENS):
        pytest.skip('cloud management commands are not supported in this environment')


def _remove_cloud_if_present(juju: jubilant.Juju, cloud_name: str) -> None:
    with contextlib.suppress(jubilant.CLIError):
        juju.cli('remove-cloud', '--client', cloud_name, include_model=False)


def _random_cloud_name() -> str:
    return f'it-cloud-{uuid.uuid4().hex[:8]}'


def _add_cloud_or_skip(
    juju: jubilant.Juju,
    name: str,
    definition: Mapping[str, Any],
) -> None:
    try:
        juju.add_cloud(name, definition, client=True)
    except jubilant.CLIError as exc:
        _skip_if_unsupported(exc)
        raise


def _show_cloud(juju: jubilant.Juju, name: str) -> str:
    return juju.cli('show-cloud', '--client', name, include_model=False)


def test_add_cloud_client(juju: jubilant.Juju):
    cloud_name = _random_cloud_name()
    endpoint = 'https://fake-endpoint-add.local:5000/v3'

    cloud_definition = {
        'clouds': {
            cloud_name: {
                'type': 'openstack',
                'auth-types': ['userpass'],
                'regions': {'dev-region': {'endpoint': endpoint}},
            }
        }
    }

    _add_cloud_or_skip(juju, cloud_name, cloud_definition)

    try:
        show_cloud = _show_cloud(juju, cloud_name)
        assert endpoint in show_cloud
    finally:
        _remove_cloud_if_present(juju, cloud_name)


def test_update_cloud_client(juju: jubilant.Juju):
    cloud_name = _random_cloud_name()

    original_endpoint = 'https://fake-endpoint-before.local:5000/v3'
    updated_endpoint = 'https://fake-endpoint-after.local:5000/v3'

    original_definition = {
        'clouds': {
            cloud_name: {
                'type': 'openstack',
                'auth-types': ['userpass'],
                'regions': {'dev-region': {'endpoint': original_endpoint}},
            }
        }
    }

    updated_definition = {
        'clouds': {
            cloud_name: {
                'type': 'openstack',
                'auth-types': ['userpass'],
                'regions': {'dev-region': {'endpoint': updated_endpoint}},
            }
        }
    }

    _add_cloud_or_skip(juju, cloud_name, original_definition)

    try:
        juju.update_cloud(cloud_name, updated_definition, client=True)
        show_cloud = _show_cloud(juju, cloud_name)
        assert updated_endpoint in show_cloud
    finally:
        _remove_cloud_if_present(juju, cloud_name)
