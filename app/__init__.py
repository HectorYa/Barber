from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import date, datetime


db = SQLAlchemy()

def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder='../templates',
        static_folder='../static'
    )

    app.jinja_env.globals.update(date=date, datetime=datetime)

    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'barberia.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.secret_key = os.urandom(24)



    db.init_app(app)

    from .routes import main as app_routes
    app.register_blueprint(app_routes)

    return app
