from nylog import app

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/nylog.db'
db = SQLAlchemy(app)

class User(db.Model):
    """
    Users who can access the log
    """

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    login = db.Column(db.String(20))
    password = db.Column(db.String(176))


posts_categories = db.Table('posts_categories', db.metadata,
                            db.Column('post', db.Integer,
                                      db.ForeignKey('post.id')),
                            db.Column('category', db.String(10),
                                      db.ForeignKey('category.name')))

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(30), nullable = False)
    slug = db.Column(db.String(30))
    content = db.Column(db.Text, nullable = False)
    created_at = db.Column(db.DateTime, nullable = False)
    covered_period = db.Column(db.Enum('day', 'week'))
    period_number = db.Column(db.Integer)

    categories = db.relationship('Post',
                                 secondary = posts_categories,
                                 backref = db.backref('posts',
                                                      lazy = 'dynamic'))

    def get_posts_for_user(self, user):
        pass

# User allowed to views posts filled under a certain category
users_categories = db.Table('users_categories', db.metadata,
                            db.Column('user', db.Integer,
                                      db.ForeignKey('user.id')),
                            db.Column('category', db.String(10),
                                      db.ForeignKey('category.name')))

class Category(db.Model):
    """
    Categories lets you decide which user can views which posts
    There is an n:m relation between category and user
    To let everyone see the posts filled under a category use 
    When a post is filled under multiple categories the => not restrictive
    """

    __tablename__ = 'category'
    name = db.Column(db.String(10), primary_key = True)

    allowed_users = db.relationship('User',
                                    secondary = users_categories,
                                    backref = db.backref('categories',
                                                      lazy = 'dynamic'))

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.Text, nullable = False)
    created_at = db.Column(db.DateTime, nullable = False)

    post_id = db.Column(db.Integer(), db.ForeignKey('post.id'),
                        nullable = False)
    post = db.relationship('Post',
                           backref = db.backref('comments', lazy = 'dynamic'))

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                          nullable = False)
    author = db.relationship('User',
                             backref = db.backref('comments', lazy = 'dynamic'))

