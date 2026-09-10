# Broker provider-secret delivery

Production external AI and shared brokerage keys are OCI Vault secrets. Broker
configuration contains secret OCIDs only. The public app and workers must have
neither these identifiers nor plaintext keys. `SERVICE_ROLE=broker` prevents
accidental client retrieval; the actual authorization boundary is OCI IAM and
the broker instance principal, not this environment flag.

Grant the broker dynamic group read access only to the required secret bundles.
The public VM must not be in that group. Secret-bundle read authorization is a
separate permission from the two credential-encryption keys' KMS permissions.
Successful secret delivery does not prove KMS access or the public VM's denial
for either key.

The broker retrieves `CURRENT` in an isolated child with an eight-second hard
deadline, disables metadata/federation/operation retries, validates bounded
BASE64 content, and never writes plaintext
to disk. Denial or malformed data fails closed without a previous-key fallback.
An accepted secret must contain just the printable API key, with no newline.
Each operation re-reads its secret so subsequent calls use the current rotation.
The in-process provider client may retain tokens needed for provider sessions.
The parent kills and reaps a delayed child, including initial instance identity
acquisition and token refresh; a timed-out request leaves no background work.

Local tests mock the SDK. Before deployment, collect real broker allow/public
deny evidence, Audit entries, rotation and revocation results as required by
`SECURITY_REMEDIATION_STATUS.md`. No such evidence is claimed by the code tests.

Official contract: [OCI SecretsClient](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/secrets/client/oci.secrets.SecretsClient.html),
[BASE64 bundle content](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/secrets/models/oci.secrets.models.Base64SecretBundleContentDetails.html).
