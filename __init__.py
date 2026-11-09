"""
The Invisible Guardian - Online AI-to-AI Audio Whisperer
Flask application factory.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "uploads", "covers"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "uploads", "secrets"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "uploads", "stego"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "uploads", "decoded"), exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "guardian.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_ROOT=os.path.join(base_dir, "uploads"),
        MAX_CONTENT_LENGTH=300 * 1024 * 1024,  # 300 MB - generous headroom for uncompressed WAV covers
        FILE_EXPIRY_HOURS=int(os.environ.get("FILE_EXPIRY_HOURS", "72")),
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.stego import stego_bp
    from app.routes.admin import admin_bp
    from app.routes.share import share_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(stego_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(share_bp)

    with app.app_context():
        db.create_all()
        _ensure_default_admin()

    return app


def _ensure_default_admin():
    """Create a default admin account on first run (dev convenience)."""
    from app.models import User
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", email="admin@guardian.local", is_admin=True)
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.commit()
