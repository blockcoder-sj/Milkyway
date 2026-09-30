"""Compatibility and malformed-key regression for the pinned JWT dependency."""

import unittest
import zlib
from unittest.mock import Mock

import jwt
from jwt.utils import base64url_encode
from urllib3.exceptions import ProtocolError
from urllib3.response import HTTPResponse, DeflateDecoder


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

    def test_deeply_nested_unverified_json_is_a_decode_error(self):
        nested = b'[' * 2000 + b'0' + b']' * 2000
        for header, payload in ((nested, b'{}'), (b'{"alg":"HS256"}', nested)):
            token = b'.'.join((base64url_encode(header), base64url_encode(payload), b'AA'))
            # PyJWT 2.14 leaked RecursionError before authenticating the token.
            with self.assertRaises(jwt.exceptions.DecodeError):
                jwt.decode(token, options={"verify_signature": False})


class HttpDependencyTests(unittest.TestCase):
    def test_deflate_eof_does_not_leave_an_infinite_stream_tail(self):
        decoder = DeflateDecoder()
        expected = b'synthetic public response' * 20
        result = decoder.decompress(zlib.compress(expected) + b'after-eof', max_length=8)
        for _ in range(100):
            if not decoder.has_unconsumed_tail:
                break
            result += decoder.decompress(b'', max_length=8)
        self.assertEqual(result, expected)
        self.assertFalse(decoder.has_unconsumed_tail)
        self.assertEqual(decoder.decompress(b'ignored after EOF'), b'')

    def test_chunk_size_line_has_a_read_bound(self):
        body = Mock()
        body.closed = False
        body.isclosed.return_value = False
        body.fp.readline.return_value = b'1;' + b'x' * 70000
        response = HTTPResponse(body=body, preload_content=False)
        with self.assertRaises(ProtocolError):
            response._update_chunk_length()
        limit = body.fp.readline.call_args.args[0]
        self.assertGreater(limit, 0)
        self.assertLessEqual(limit, 65537)
        body.close.assert_called()


if __name__ == "__main__":
    unittest.main()
