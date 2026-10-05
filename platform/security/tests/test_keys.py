"""
platform.security.keys had no tests at all before this file -- none of the
4 backends (local_dev/aws_kms/azure_key_vault/gcp_kms) were exercised.
Azure/GCP are mocked at the SDK boundary (no real account available this
session) -- these tests verify THIS module's own logic (digest computation,
base64 wire framing, resource-name handling, verify-returns-False-not-
raises on a bad signature), not the real cloud round trip.
"""
import base64
from unittest.mock import MagicMock, patch

import pytest

from platform.security.keys import (
    AWSKmsKeyStore,
    AzureKeyVaultKeyStore,
    GCPKeyStore,
    LocalDevKeyStore,
    get_keystore,
    reset_keystore,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_keystore()
    yield
    reset_keystore()


class TestFactory:
    def test_defaults_to_local_dev(self, monkeypatch, tmp_path):
        monkeypatch.delenv("PLATFORM_KMS_BACKEND", raising=False)
        monkeypatch.setenv("PLATFORM_KEY_DIR", str(tmp_path))
        ks = get_keystore()
        assert ks.backend_name == "local_dev"

    def test_unknown_backend_raises(self, monkeypatch):
        monkeypatch.setenv("PLATFORM_KMS_BACKEND", "oracle_vault")
        with pytest.raises(ValueError, match="Unknown PLATFORM_KMS_BACKEND"):
            get_keystore()

    def test_cached_across_calls(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PLATFORM_KMS_BACKEND", "local_dev")
        monkeypatch.setenv("PLATFORM_KEY_DIR", str(tmp_path))
        assert get_keystore() is get_keystore()


class TestLocalDevKeyStore:
    def test_sign_and_verify_round_trip(self, tmp_path):
        ks = LocalDevKeyStore(key_dir=str(tmp_path))
        data = b"invoice-hash-abc123"
        sig = ks.sign(data, "test-key")
        assert ks.verify(data, sig, "test-key") is True

    def test_verify_rejects_tampered_data(self, tmp_path):
        ks = LocalDevKeyStore(key_dir=str(tmp_path))
        sig = ks.sign(b"original", "test-key")
        assert ks.verify(b"tampered", sig, "test-key") is False

    def test_wrap_and_unwrap_round_trip(self, tmp_path):
        ks = LocalDevKeyStore(key_dir=str(tmp_path))
        plaintext = b"super-secret-dek"
        wrapped = ks.wrap(plaintext, "wrap-key")
        assert ks.unwrap(wrapped, "wrap-key") == plaintext

    def test_keys_persist_across_instances(self, tmp_path):
        ks1 = LocalDevKeyStore(key_dir=str(tmp_path))
        sig = ks1.sign(b"data", "persisted-key")
        ks2 = LocalDevKeyStore(key_dir=str(tmp_path))
        assert ks2.verify(b"data", sig, "persisted-key") is True


class TestAWSKmsKeyStore:
    def test_requires_boto3(self):
        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(RuntimeError, match="requires boto3"):
                AWSKmsKeyStore()

    def test_sign_calls_kms_with_ecdsa_sha256(self):
        with patch.dict("sys.modules", {"boto3": MagicMock()}):
            ks = AWSKmsKeyStore(region="us-east-1")
            fake_client = MagicMock()
            fake_client.sign.return_value = {"Signature": b"sig-bytes"}
            ks._client = fake_client
            result = ks.sign(b"data", "alias/my-key")
            assert result == b"sig-bytes"
            fake_client.sign.assert_called_once_with(
                KeyId="alias/my-key", Message=b"data", MessageType="RAW",
                SigningAlgorithm="ECDSA_SHA_256",
            )

    def test_verify_returns_false_on_exception(self):
        with patch.dict("sys.modules", {"boto3": MagicMock()}):
            ks = AWSKmsKeyStore(region="us-east-1")
            fake_client = MagicMock()
            fake_client.verify.side_effect = RuntimeError("boom")
            ks._client = fake_client
            assert ks.verify(b"data", b"sig", "alias/my-key") is False

    def test_wrap_unwrap_base64_framing(self):
        with patch.dict("sys.modules", {"boto3": MagicMock()}):
            ks = AWSKmsKeyStore(region="us-east-1")
            fake_client = MagicMock()
            fake_client.encrypt.return_value = {"CiphertextBlob": b"raw-blob"}
            fake_client.decrypt.return_value = {"Plaintext": b"plain"}
            ks._client = fake_client
            wrapped = ks.wrap(b"plain", "alias/my-key")
            assert base64.b64decode(wrapped) == b"raw-blob"
            assert ks.unwrap(wrapped, "alias/my-key") == b"plain"


class TestAzureKeyVaultKeyStore:
    def test_requires_sdk(self):
        with patch.dict("sys.modules", {"azure.identity": None}):
            with pytest.raises(RuntimeError, match="requires azure-identity"):
                AzureKeyVaultKeyStore(vault_url="https://x.vault.azure.net")

    def test_requires_vault_url(self, monkeypatch):
        monkeypatch.delenv("AZURE_KEY_VAULT_URL", raising=False)
        with patch("azure.identity.DefaultAzureCredential"), \
             patch("azure.keyvault.keys.crypto.CryptographyClient"):
            with pytest.raises(RuntimeError, match="AZURE_KEY_VAULT_URL"):
                AzureKeyVaultKeyStore()

    def test_key_identifier_builds_from_bare_name(self):
        with patch("azure.identity.DefaultAzureCredential"), \
             patch("azure.keyvault.keys.crypto.CryptographyClient"):
            ks = AzureKeyVaultKeyStore(vault_url="https://myvault.vault.azure.net")
            assert ks._key_identifier("mykey") == "https://myvault.vault.azure.net/keys/mykey"
            full = "https://myvault.vault.azure.net/keys/mykey/abc123"
            assert ks._key_identifier(full) == full

    def test_sign_hashes_then_signs_digest(self):
        import hashlib

        with patch("azure.identity.DefaultAzureCredential"), \
             patch("azure.keyvault.keys.crypto.CryptographyClient") as MockClient:
            fake_client = MagicMock()
            fake_client.sign.return_value = MagicMock(signature=b"es256-sig")
            MockClient.return_value = fake_client
            ks = AzureKeyVaultKeyStore(vault_url="https://myvault.vault.azure.net")
            result = ks.sign(b"payload", "mykey")
            assert result == b"es256-sig"
            digest_sent = fake_client.sign.call_args[0][1]
            assert digest_sent == hashlib.sha256(b"payload").digest()

    def test_verify_returns_false_on_exception(self):
        with patch("azure.identity.DefaultAzureCredential"), \
             patch("azure.keyvault.keys.crypto.CryptographyClient") as MockClient:
            fake_client = MagicMock()
            fake_client.verify.side_effect = RuntimeError("boom")
            MockClient.return_value = fake_client
            ks = AzureKeyVaultKeyStore(vault_url="https://myvault.vault.azure.net")
            assert ks.verify(b"data", b"sig", "mykey") is False

    def test_wrap_unwrap_base64_framing(self):
        with patch("azure.identity.DefaultAzureCredential"), \
             patch("azure.keyvault.keys.crypto.CryptographyClient") as MockClient:
            fake_client = MagicMock()
            fake_client.encrypt.return_value = MagicMock(ciphertext=b"raw-ct")
            fake_client.decrypt.return_value = MagicMock(plaintext=b"plain")
            MockClient.return_value = fake_client
            ks = AzureKeyVaultKeyStore(vault_url="https://myvault.vault.azure.net")
            wrapped = ks.wrap(b"plain", "mykey")
            assert base64.b64decode(wrapped) == b"raw-ct"
            assert ks.unwrap(wrapped, "mykey") == b"plain"


class TestGCPKeyStore:
    def test_requires_sdk(self):
        with patch.dict("sys.modules", {"google.cloud.kms": None, "google.cloud": None}):
            with pytest.raises(RuntimeError, match="requires google-cloud-kms"):
                GCPKeyStore()

    def test_sign_sends_sha256_digest(self):
        import hashlib

        with patch("google.cloud.kms.KeyManagementServiceClient") as MockClient:
            fake_client = MagicMock()
            fake_client.asymmetric_sign.return_value = MagicMock(signature=b"ec-sig")
            MockClient.return_value = fake_client
            ks = GCPKeyStore()
            key_name = "projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1"
            result = ks.sign(b"payload", key_name)
            assert result == b"ec-sig"
            call_kwargs = fake_client.asymmetric_sign.call_args.kwargs["request"]
            assert call_kwargs["name"] == key_name
            assert call_kwargs["digest"]["sha256"] == hashlib.sha256(b"payload").digest()

    def test_verify_fetches_and_caches_public_key(self):
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        priv = ec.generate_private_key(ec.SECP256R1())
        pem = priv.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        with patch("google.cloud.kms.KeyManagementServiceClient") as MockClient:
            fake_client = MagicMock()
            fake_client.get_public_key.return_value = MagicMock(pem=pem)
            MockClient.return_value = fake_client
            ks = GCPKeyStore()
            key_name = "projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1"
            sig = priv.sign(b"data", ec.ECDSA(hashes.SHA256()))

            assert ks.verify(b"data", sig, key_name) is True
            assert ks.verify(b"tampered", sig, key_name) is False
            # cached: get_public_key only called once across both verify() calls
            fake_client.get_public_key.assert_called_once()

    def test_wrap_unwrap_base64_framing(self):
        with patch("google.cloud.kms.KeyManagementServiceClient") as MockClient:
            fake_client = MagicMock()
            fake_client.encrypt.return_value = MagicMock(ciphertext=b"raw-ct")
            fake_client.decrypt.return_value = MagicMock(plaintext=b"plain")
            MockClient.return_value = fake_client
            ks = GCPKeyStore()
            key_name = "projects/p/locations/l/keyRings/r/cryptoKeys/k"
            wrapped = ks.wrap(b"plain", key_name)
            assert base64.b64decode(wrapped) == b"raw-ct"
            assert ks.unwrap(wrapped, key_name) == b"plain"
