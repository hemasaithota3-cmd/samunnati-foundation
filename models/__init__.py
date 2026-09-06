from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access the admin area."
login_manager.login_message_category = "warning"

# Import models AFTER db is defined so they can `from models import db`.
from models.user import Admin  # noqa: E402,F401
from models.guidance import GuidanceRequest  # noqa: E402,F401
from models.mentor import MentorApplication  # noqa: E402,F401
from models.volunteer import VolunteerApplication  # noqa: E402,F401
from models.notification import Notification  # noqa: E402,F401
from models.email_log import EmailLog  # noqa: E402,F401
