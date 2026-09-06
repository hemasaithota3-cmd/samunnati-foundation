import logging
import os

from flask import Flask, render_template
from flask_mail import Mail
from flask_wtf import CSRFProtect

from config import Config
from models import db, login_manager
from routes import register_blueprints

csrf = CSRFProtect()
mail = Mail()  # Global Flask-Mail instance


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)  # Initialize Flask-Mail with app configuration

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import Admin
        return db.session.get(Admin, int(user_id))

    register_blueprints(app)

    # ---- Template globals available on every page ----
    @app.context_processor
    def inject_globals():
        from services.notification_service import unread_count
        from flask_login import current_user
        unread = unread_count() if current_user.is_authenticated else 0
        return {
            "site_name": app.config["SITE_NAME"],
            "current_year": __import__("datetime").datetime.now().year,
            "unread_notifications": unread,
            "notification_poll_interval": app.config["NOTIFICATION_POLL_INTERVAL_MS"],
        }

    # ---- Error handlers: never leak internals ----
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error: %s", e)
        return render_template("errors/500.html"), 500

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))