class Base:
    DEBUG = False
    ENV = 'production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'

class Development(Base):
    DEBUG = True
    ENV = 'development'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # mysql+pymysql://<username>:<password>@<host_ip>:<port>/<database_name>
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://<username>:<password>@<host_ip>:<port>/<database_name>'