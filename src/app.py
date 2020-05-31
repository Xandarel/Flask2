from flask import Flask


from src.blueprints.ads import bp as ads_bp
from src.blueprints.auth import bp as auth_bp
from src.blueprints.users import bp as users_bp
from src.blueprints.user_ads import bp as user_ads_bp
from src.database import db


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.register_blueprint(ads_bp, url_prefix='/ads')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(user_ads_bp, url_prefix='/users')
    db.init_app(app)
    return app
