"""Compatibility and malformed-key regression for the pinned JWT dependency."""

import unittest

import jwt


class JwtDependencyTests(unittest.TestCase):
    def test_supported_hmac_token_round_trip(self):
        key = b"milkyway-synthetic-test-key-32-bytes"
        token = jwt.encode({"sub": "synthetic-user"}, key, algorithm="HS256")
        self.assertEqual(jwt.decode(token, key, algorithms=["HS256"])["sub"], "synthetic-user")

    def test_empty_symmetric_jwk_is_rejected(self):
        # PyJWT 2.13.0 accepted empty material through PyJWK while rejecting
        # the equivalent raw key (CVE-2026-102266). No real credentials/network.
        with self.assertRaises(jwt.exceptions.InvalidKeyError):
            jwk = jwt.PyJWK.from_dict({"kty": "oct", "k": "", "alg": "HS256"})
            jwt.decode("eyJhbGciOiJIUzI1NiJ9.e30.AA", jwk, algorithms=["HS256"])


if __name__ == "__main__":
    unittest.main()
