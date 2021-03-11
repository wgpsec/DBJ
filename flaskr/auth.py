import functools
from flask_pymongo import PyMongo
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,current_app
)
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    mongo = PyMongo(current_app)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = mongo.db.user.find_one({'username':username})

        if user is None:
            error = '用户不存在'
        elif user['password'] != password:
            error = '密码错误'

        if error is None:
            session.clear()
            session['user_id'] = user['uid']
            return redirect(url_for('admin.index'))

        flash(error)

    return render_template('admin/login.html')

@bp.before_app_request
def load_logged_in_user():
    mongo = PyMongo(current_app)
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = mongo.db.user.find_one({'uid':user_id})

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view