import sys
from nylog import app, db, new_user

if __name__ == '__main__':
    if 'create_db' in sys.argv:
        db.create_all()
    if 'create_user' in sys.argv:
        from getpass import getpass

        login = input('Login [%s]: ' % app.config.get('NYLOG_ADMIN', ''))
        if login is '':
            login = app.config['NYLOG_ADMIN']

        def get_password():
            return getpass('Password: '), getpass('Confirm Password: ')

        password, confirm = get_password()
        while password != confirm:
            print("Passwords didn't match, please try again")
            password, confirm = get_password()
        
        user = new_user(login, password)
        db.session.add(user)
        db.session.commit()
    else:
        app.run(host = '0.0.0.0')
