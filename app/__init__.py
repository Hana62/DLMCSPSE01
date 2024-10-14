from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Initialize extensions without circular import issues
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize the extensions with the app instance
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import routes, models after initializing app (deferred import to avoid circular import)
    with app.app_context():
        from . import routes  # Import routes after app is initialized
        from .models import User  # Import models after app is initialized
        db.create_all()  # Create tables after everything is set

    return app

# Define the user loader here to avoid circular imports
@login_manager.user_loader
def load_user(user_id):
    from .models import User  # Import within the function to avoid circular import
    return User.query.get(int(user_id))
