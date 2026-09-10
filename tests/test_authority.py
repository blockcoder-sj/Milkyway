"""Independent issuer controls; live PostgreSQL ACL/RLS are tested separately."""

import datetime as dt
import os
import unittest
from dataclasses import replace
from unittest.mock import patch

os.environ.setdefault("APP_ENV", "development")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloud_app import authority
from cloud_app.config import get_settings
from cloud_app.database import AuthoritySession, Base, Invitation, OperationPermit, User, utcnow


class IndependentAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()
        self.settings = replace(get_settings(), session_secret="Independent-Issuer-Secret-0123456789", login_account_attempts=2)
        self.invite = "Invitation-For-One-Member-0123456789"
        self.password = "Member-Password-0123456789"
        self.session.add(Invitation.create(
            token=self.invite, email="one@example.com", secret=self.settings.session_secret,
            expires_at=utcnow() + dt.timedelta(hours=1),
        ))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def register(self):
        return authority.register_member(
            self.session, self.settings, email="one@example.com", display_name="One Member",
            password=self.password, invite_code=self.invite,
        )

    def test_invitation_is_bound_to_email_and_rejected_before_password_hashing(self):
        with patch.object(authority, "hash_password") as hashing:
            with self.assertRaises(HTTPException) as raised:
                authority.register_member(self.session, self.settings, email="other@example.com", display_name="Other", password=self.password, invite_code=self.invite)
        self.assertEqual(raised.exception.status_code, 403)
        hashing.assert_not_called()
        self.assertEqual(self.session.query(User).count(), 0)
        result = self.register()
        self.assertEqual(result["user"]["email"], "one@example.com")
        self.assertIsNotNone(self.session.query(Invitation).one().redeemed_at)

    def test_only_an_issued_raw_token_authenticates_and_revocation_is_durable(self):
        result = self.register()
        stored = self.session.query(AuthoritySession).one()
        self.assertNotEqual(result["session_token"], stored.token_hash)
        for forged in (stored.token_hash, "A" * 43, result["user"]["id"]):
            with self.subTest(forged=forged), self.assertRaises(HTTPException):
                authority.principal(self.session, forged)
        user, _record = authority.principal(self.session, result["session_token"], result["csrf"])
        self.assertEqual(user.id, result["user"]["id"])
        with self.assertRaises(HTTPException):
            authority.revoke_session(self.session, result["session_token"], "wrong-csrf")
        authority.revoke_session(self.session, result["session_token"], result["csrf"])
        with self.assertRaises(HTTPException):
            authority.principal(self.session, result["session_token"])

    def test_expiration_and_account_disable_are_checked_independently(self):
        result = self.register()
        record = self.session.query(AuthoritySession).one()
        record.expires_at = utcnow() - dt.timedelta(seconds=1)
        self.session.commit()
        with self.assertRaises(HTTPException):
            authority.principal(self.session, result["session_token"])
        result = authority.login_member(self.session, self.settings, email="one@example.com", password=self.password)
        self.session.get(User, result["user"]["id"]).active = False
        self.session.commit()
        with self.assertRaises(HTTPException):
            authority.principal(self.session, result["session_token"])

    def test_targeted_bad_passwords_do_not_lock_out_a_valid_password(self):
        self.register()
        for _ in range(4):
            with self.assertRaises(HTTPException):
                authority.login_member(self.session, self.settings, email="one@example.com", password="wrong-password")
        result = authority.login_member(self.session, self.settings, email="one@example.com", password=self.password)
        self.assertEqual(result["user"]["email"], "one@example.com")

    def test_permit_needs_a_live_member_and_binds_payload_nonce_and_one_use(self):
        identity = self.register()
        kwargs = dict(raw_token=identity["session_token"], csrf=identity["csrf"], prompt="Build a cautious equity strategy", nonce="n" * 32)
        for override in ({"raw_token": "x" * 43}, {"csrf": "wrong"}):
            with self.assertRaises(HTTPException):
                authority.issue_ai_permit(self.session, self.settings, **(kwargs | override))
        permit = authority.issue_ai_permit(self.session, self.settings, **kwargs)
        with self.assertRaises(HTTPException):
            authority.issue_ai_permit(self.session, self.settings, **kwargs)
        self.session.rollback()
        with self.assertRaises(HTTPException):
            authority.consume_ai_permit(self.session, raw_permit=permit, prompt="A different strategy")
        self.session.rollback()
        owner = authority.consume_ai_permit(self.session, raw_permit=permit, prompt=kwargs["prompt"])
        self.assertEqual(owner, identity["user"]["id"])
        self.session.close()
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()
        with self.assertRaises(HTTPException):
            authority.consume_ai_permit(self.session, raw_permit=permit, prompt=kwargs["prompt"])

    def test_permit_expiry_revocation_and_durable_member_budget(self):
        identity = self.register()
        tokens = [authority.issue_ai_permit(self.session, self.settings,
            raw_token=identity["session_token"], csrf=identity["csrf"], prompt="Build a strategy",
            nonce=str(i).zfill(32)) for i in range(10)]
        with self.assertRaises(HTTPException) as denied:
            authority.issue_ai_permit(self.session, self.settings,
                raw_token=identity["session_token"], csrf=identity["csrf"], prompt="Build a strategy", nonce="z" * 32)
        self.assertEqual(denied.exception.status_code, 429)
        self.session.rollback()
        record = self.session.get(OperationPermit, authority.token_hash(tokens[0]))
        record.expires_at = utcnow() - dt.timedelta(seconds=1)
        self.session.commit()
        with self.assertRaises(HTTPException):
            authority.consume_ai_permit(self.session, raw_permit=tokens[0], prompt="Build a strategy")
        self.session.rollback()
        authority.revoke_session(self.session, identity["session_token"], identity["csrf"])
        with self.assertRaises(HTTPException):
            authority.consume_ai_permit(self.session, raw_permit=tokens[1], prompt="Build a strategy")
