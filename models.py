from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobs = db.relationship("StegoJob", backref="owner", lazy="dynamic",
                            foreign_keys="StegoJob.user_id")

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class StegoJob(db.Model):
    """One encode operation: a secret hidden inside a cover, producing a stego file."""
    __tablename__ = "stego_jobs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    cover_filename = db.Column(db.String(255))
    secret_filename = db.Column(db.String(255))
    stego_filename = db.Column(db.String(255), unique=True)

    snr_db = db.Column(db.Float)
    mse = db.Column(db.Float)
    spectrogram_similarity = db.Column(db.Float)
    payload_bytes = db.Column(db.Integer)
    cover_capacity_bytes = db.Column(db.Integer)
    train_loss_final = db.Column(db.Float)
    encode_seconds = db.Column(db.Float)

    passphrase_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    shares = db.relationship("FileShare", backref="job", lazy="dynamic",
                              cascade="all, delete-orphan")
    decode_logs = db.relationship("DecodeLog", backref="job", lazy="dynamic",
                                   cascade="all, delete-orphan")

    def set_passphrase(self, raw):
        self.passphrase_hash = generate_password_hash(raw) if raw else None

    def check_passphrase(self, raw):
        if not self.passphrase_hash:
            return True
        return check_password_hash(self.passphrase_hash, raw or "")

    def is_expired(self):
        return self.expires_at is not None and datetime.utcnow() > self.expires_at

    def mark_expiry(self, hours):
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)


class FileShare(db.Model):
    """Sharing a stego job with another registered user."""
    __tablename__ = "file_shares"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("stego_jobs.id"), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    shared_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shared_with = db.relationship("User", foreign_keys=[shared_with_id])
    shared_by = db.relationship("User", foreign_keys=[shared_by_id])


class ShareLink(db.Model):
    """A one-time, no-login-required link a sender can hand to a friend."""
    __tablename__ = "share_links"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("stego_jobs.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    used_at = db.Column(db.DateTime)
    decoded_filename = db.Column(db.String(255))

    job = db.relationship("StegoJob")
    created_by = db.relationship("User")

    def is_expired(self):
        return self.expires_at is not None and datetime.utcnow() > self.expires_at

    def is_used(self):
        return self.used_at is not None

    def is_valid(self):
        return not self.is_expired() and not self.is_used()

    def mark_expiry(self, hours=24):
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)


class DecodeLog(db.Model):
    """Every decode attempt, successful or not - for the admin monitoring view."""
    __tablename__ = "decode_logs"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("stego_jobs.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    guest_note = db.Column(db.String(120))
    success = db.Column(db.Boolean, default=False)
    decode_seconds = db.Column(db.Float)
    reconstruction_note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
