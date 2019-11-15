import pytest
import datetime
from unittest.mock import patch, Mock, MagicMock
from string import Template

import requests

import tfc_client
from tfc_client.models.workspace import VCSRepoModel

def get_organization_json(org_id):
    SAMPLE_ORGANIZATION = Template("""{
        "data": {
            "id": "$org_id",
            "type": "organizations",
            "attributes": {
            "name": "$org_id",
            "cost-estimation-enabled": false,
            "created-at": "2017-09-07T14:34:40.492Z",
            "email": "user@example.com",
            "session-timeout": null,
            "session-remember": null,
            "collaborator-auth-policy": "password",
            "enterprise-plan": "pro",
            "permissions": {
                "can-update": true,
                "can-destroy": true,
                "can-create-team": true,
                "can-create-workspace": true,
                "can-update-oauth": true,
                "can-update-api-token": true,
                "can-update-sentinel": true,
                "can-traverse": true,
                "can-create-workspace-migration": true
            }
            },
            "links": {
            "self": "/api/v2/organizations/$org_id"
            }
        }
    }""")
    return SAMPLE_ORGANIZATION.substitute(org_id=org_id)


def get_workspace_json(name, org_id):
    ws_id = f"ws-{name}"
    SAMPLE_WORKSPACE = Template("""{
        "data": {
            "id": "$ws_id",
            "type": "workspaces",
            "attributes": {
            "auto-apply": false,
            "can-queue-destroy-plan": true,
            "created-at": "2017-11-02T23:55:16.142Z",
            "description": null,
            "environment": "default",
            "file-triggers-enabled": true,
            "locked": false,
            "name": "$name",
            "permissions": {
                "can-update": true,
                "can-destroy": false,
                "can-queue-destroy": false,
                "can-queue-run": false,
                "can-update-variable": false,
                "can-lock": false,
                "can-read-settings": true
            },
            "queue-all-runs": false,
            "source": "tfe-ui",
            "source-name": null,
            "source-url": null,
            "terraform-version": "0.10.8",
            "trigger-prefixes": [],
            "vcs-repo": {
                "identifier": "skierkowski/terraform-test-proj",
                "branch": "",
                "oauth-token-id": "ot-hmAyP66qk2AMVdbJ",
                "ingress-submodules": false
            },
            "working-directory": null
            },
            "relationships": {
            "organization": {
                "data": {
                "id": "$org_id",
                "type": "organizations"
                }
            },
            "ssh-key": {
                "data": null
            },
            "latest-run": {
                "data": null
            }
            },
            "links": {
            "self": "/api/v2/organizations/$org_id/workspaces/$name"
            }
        }
    }""")
    return SAMPLE_WORKSPACE.substitute(name=name, org_id=org_id, ws_id=ws_id)

def register_requests_mock(requests_mock, method, url, text):
    getattr(requests_mock, method)(url, text=text)

class TestTFCClient(object):
    def test_get(self, requests_mock):
        org_id = "hashicorp"
        # requests_mock.get("/api/v2/organizations/hashicorp", text=get_organization_json(org_id=org_id))
        register_requests_mock(requests_mock, "get", "/api/v2/organizations/hashicorp", text=get_organization_json(org_id=org_id))
        tfc = tfc_client.TFCClient(token="token")
        org = tfc.get("organization", id=org_id)
        assert org.name == org_id
        assert isinstance(org.created_at, datetime.datetime)

class TestTFCOrganization(object):
    def test_create_workspace(self, requests_mock):
        org_id = "hashicorp"
        ws_name = "workspace1"
        requests_mock.get(f"/api/v2/organizations/{org_id}", text=get_organization_json(org_id=org_id))
        requests_mock.post(f"/api/v2/organizations/{org_id}/workspaces", text=get_workspace_json(name=ws_name, org_id=org_id))
        tfc = tfc_client.TFCClient(token="token")
        org = tfc.get("organization", id=org_id)
        vcs_repo = VCSRepoModel(
            identifier="skierkowski/terraform-test-proj",
            oauth_token_id="ot-hmAyP66qk2AMVdbJ",
            branch="",
        )
        ws = org.create("workspace", name=ws_name, terraform_version="0.10.8", vcs_repo=vcs_repo)
        assert ws.name == ws_name
        assert isinstance(ws.created_at, datetime.datetime)
