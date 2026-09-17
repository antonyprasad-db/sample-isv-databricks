"""Unit tests for the config and gateway-wiring guarantees this sample relies on.

Companion to test_cleanup_contract.py. These cover the small, high-leverage pieces
whose failure is silent or only surfaces mid-deployment against a live account:

    - require_databricks_config()   fail-fast on missing env, naming every gap
    - genie_mcp_url()               the exact Databricks-managed MCP endpoint shape
    - create_credential_provider()  the fail-fast guard on a missing secret ARN, and
                                    the two response shapes it must accept
    - grant_oauth_permissions()     the IAM policy shape -- notably that the secret
                                    read is scoped to one ARN and never falls back to "*"

Standard library only, so the sample gains no test dependency:

    python -m unittest test_config_and_gateway -v
"""

import contextlib
import io
import json
import unittest
from unittest import mock

import config
import deploy
from gateway_setup import GatewaySetup


class RequireDatabricksConfigTest(unittest.TestCase):
    """require_databricks_config() must fail fast and name every missing variable."""

    # The four values the function guards, all read from module globals at call time.
    _ALL_PRESENT = {
        "DATABRICKS_HOST": "https://dbc-x.cloud.databricks.com",
        "DATABRICKS_CLIENT_ID": "client-id",
        "DATABRICKS_CLIENT_SECRET": "secret",
        "GENIE_SPACE_ID": "space-id",
    }

    def _patch(self, values):
        """Patch the four config globals for the duration of one test."""
        for name, value in values.items():
            patcher = mock.patch.object(config, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_all_present_does_not_raise(self):
        self._patch(self._ALL_PRESENT)
        config.require_databricks_config()  # no exception

    def test_each_missing_value_is_named(self):
        for missing in self._ALL_PRESENT:
            with self.subTest(missing=missing):
                values = dict(self._ALL_PRESENT, **{missing: ""})
                self._patch(values)
                with self.assertRaises(SystemExit) as ctx:
                    config.require_databricks_config()
                self.assertIn(missing, str(ctx.exception))

    def test_all_missing_are_listed_together(self):
        self._patch({name: "" for name in self._ALL_PRESENT})
        with self.assertRaises(SystemExit) as ctx:
            config.require_databricks_config()
        message = str(ctx.exception)
        for name in self._ALL_PRESENT:
            self.assertIn(name, message)


class GenieMcpUrlTest(unittest.TestCase):
    """genie_mcp_url() must produce the Databricks-managed Genie MCP endpoint."""

    def test_builds_managed_endpoint_for_space(self):
        with mock.patch.object(config, "DATABRICKS_HOST", "https://dbc-x.cloud.databricks.com"), \
             mock.patch.object(config, "GENIE_SPACE_ID", "01f000abc"):
            self.assertEqual(
                config.genie_mcp_url(),
                "https://dbc-x.cloud.databricks.com/api/2.0/mcp/genie/01f000abc",
            )

    def test_reflects_configured_space(self):
        with mock.patch.object(config, "DATABRICKS_HOST", "https://host"), \
             mock.patch.object(config, "GENIE_SPACE_ID", "space-42"):
            self.assertTrue(config.genie_mcp_url().endswith("/api/2.0/mcp/genie/space-42"))


class CreateCredentialProviderSecretArnTest(unittest.TestCase):
    """create_credential_provider() resolves the secret ARN across response shapes,
    and fails loudly rather than silently dropping the secret-read grant."""

    class _FakeAgentCore:
        def __init__(self, response):
            self._response = response

        def create_oauth2_credential_provider(self, **kwargs):
            return self._response

    def _create(self, fake):
        """Call create_credential_provider, swallowing its progress prints."""
        with contextlib.redirect_stdout(io.StringIO()):
            return deploy.create_credential_provider(fake)

    def test_flat_secret_arn(self):
        fake = self._FakeAgentCore(
            {"credentialProviderArn": "arn:prov", "secretArn": "arn:aws:secretsmanager:...:secret:x"}
        )
        provider_arn, secret_arn = self._create(fake)
        self.assertEqual(provider_arn, "arn:prov")
        self.assertEqual(secret_arn, "arn:aws:secretsmanager:...:secret:x")

    def test_nested_client_secret_arn(self):
        fake = self._FakeAgentCore(
            {"credentialProviderArn": "arn:prov", "clientSecretArn": {"secretArn": "arn:nested"}}
        )
        _, secret_arn = self._create(fake)
        self.assertEqual(secret_arn, "arn:nested")

    def test_flat_arn_wins_over_nested(self):
        fake = self._FakeAgentCore(
            {
                "credentialProviderArn": "arn:prov",
                "secretArn": "arn:flat",
                "clientSecretArn": {"secretArn": "arn:nested"},
            }
        )
        _, secret_arn = self._create(fake)
        self.assertEqual(secret_arn, "arn:flat")

    def test_missing_secret_arn_aborts(self):
        fake = self._FakeAgentCore({"credentialProviderArn": "arn:prov"})
        with self.assertRaises(SystemExit) as ctx:
            self._create(fake)
        self.assertIn("secret ARN", str(ctx.exception))


class GrantOauthPermissionsPolicyTest(unittest.TestCase):
    """grant_oauth_permissions() writes an IAM policy that (a) grants the workload-token
    and token-exchange actions and (b) scopes the secret read to one ARN, never '*'."""

    class _FakeIam:
        def __init__(self):
            self.put_role_policy_kwargs = None

        def put_role_policy(self, **kwargs):
            self.put_role_policy_kwargs = kwargs

    def _run(self, secret_arn):
        """Invoke the method on a GatewaySetup built without boto3, return the policy dict."""
        setup = GatewaySetup.__new__(GatewaySetup)  # skip __init__ (it calls boto3 + STS)
        setup.region = "us-west-2"
        setup.account_id = "123456789012"
        setup.iam = self._FakeIam()
        # grant_oauth_permissions sleeps 10s for IAM propagation and prints progress;
        # skip the sleep and swallow the print in a unit test.
        with mock.patch("gateway_setup.time.sleep"), contextlib.redirect_stdout(io.StringIO()):
            setup.grant_oauth_permissions(
                role_arn="arn:aws:iam::123456789012:role/DatabricksGenieGatewayRole",
                policy_name="DatabricksGenieOAuthAccess",
                provider_arn="arn:aws:bedrock-agentcore:us-west-2:123456789012:token-vault/default/oauth2credentialprovider/x",
                secret_arn=secret_arn,
            )
        kwargs = setup.iam.put_role_policy_kwargs
        self.assertIsNotNone(kwargs, "put_role_policy was never called")
        return kwargs, json.loads(kwargs["PolicyDocument"])

    def test_policy_is_well_formed(self):
        kwargs, doc = self._run(secret_arn="arn:aws:secretsmanager:us-west-2:123456789012:secret:db")
        self.assertEqual(kwargs["RoleName"], "DatabricksGenieGatewayRole")
        self.assertEqual(kwargs["PolicyName"], "DatabricksGenieOAuthAccess")
        self.assertEqual(doc["Version"], "2012-10-17")

    def test_grants_workload_and_token_exchange_actions(self):
        _, doc = self._run(secret_arn="arn:aws:secretsmanager:us-west-2:123456789012:secret:db")
        actions = set()
        for stmt in doc["Statement"]:
            action = stmt["Action"]
            actions.update(action if isinstance(action, list) else [action])
        self.assertIn("bedrock-agentcore:GetWorkloadAccessToken", actions)
        self.assertIn("bedrock-agentcore:GetWorkloadAccessTokenForJWT", actions)
        self.assertIn("bedrock-agentcore:GetResourceOauth2Token", actions)

    def test_secret_read_scoped_to_arn_not_wildcard(self):
        arn = "arn:aws:secretsmanager:us-west-2:123456789012:secret:db"
        _, doc = self._run(secret_arn=arn)
        secret_stmts = [
            s for s in doc["Statement"] if "secretsmanager:GetSecretValue" in _actions_of(s)
        ]
        self.assertEqual(len(secret_stmts), 1)
        self.assertEqual(secret_stmts[0]["Resource"], arn)
        # The whole reason the ARN is threaded through: never grant read on every secret.
        self.assertNotIn("*", _resources_of(secret_stmts[0]))

    def test_no_secret_statement_when_arn_absent(self):
        _, doc = self._run(secret_arn="")
        for stmt in doc["Statement"]:
            self.assertNotIn("secretsmanager:GetSecretValue", _actions_of(stmt))


def _actions_of(statement):
    action = statement.get("Action", [])
    return action if isinstance(action, list) else [action]


def _resources_of(statement):
    resource = statement.get("Resource", [])
    return resource if isinstance(resource, list) else [resource]


if __name__ == "__main__":
    unittest.main()
