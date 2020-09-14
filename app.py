from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_cors import CORS
from models import db

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['ENV'] = 'development'
app.config['DEBUG'] = True 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"

db.init_app(app)
Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)

CORS(app)

@app.route("/")
def main():
    return render_template('index.html')

if __name__ == "__main__":
    manager.run()