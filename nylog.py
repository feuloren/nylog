import sys
from nylog import app, db

if __name__ == '__main__':
    if 'create_db' in sys.argv:
        db.create_all()
    else:
        app.run(host = '0.0.0.0')
