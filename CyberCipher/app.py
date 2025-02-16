from flask import Flask
from home import home
from ideator.idea import idbp, db
from logo_maker.logo import lgbp

app = Flask(__name__)

app.register_blueprint(home)
app.register_blueprint(idbp)
app.register_blueprint(lgbp)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the Flask app
db.init_app(app)

# Register the Blueprint
app.register_blueprint(idbp)

# Create the database tables (optional, run this once)
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
