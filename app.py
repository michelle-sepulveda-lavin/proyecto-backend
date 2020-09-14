from flask import Flask, jsonify, request, render_template
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_cors import CORS
from config import Development
from models import db

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config.from_object(Development)

db.init_app(app)
Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)


@app.route("/")
def main():
    return render_template('index.html')

if __name__ == "__main__":
    manager.run()