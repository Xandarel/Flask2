from flask import (
    Blueprint,
    request,
    session,
)
from werkzeug.security import check_password_hash

from src.database import db


bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login():
    request_json = request.json
    email = request_json.get('email')
    password = request_json.get('password')

    if not email or not password:
        return 'not user or password', 401

    with db.connection as con:
        cur = con.execute(
            'SELECT * '
            'FROM account '
            'WHERE email = ?',
            (email,),
        )
        user = cur.fetchone()

    if user is None:
        return 'not user', 403

    if not check_password_hash(user['password'], password):
        return 'bad password', 403
    session['id'] = user['id']
    return '', 200


@bp.route('/logout', methods=['POST'])
def logout():
    session['id'] = None
    return '', 200
