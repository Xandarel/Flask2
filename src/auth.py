from functools import wraps

from flask import session

from src.database import db


def auth_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return '', 403
        with db.connection as con:
            cur = con.execute(
                'SELECT id, username '
                'FROM user '
                'WHERE id = ?',
                (user_id,),
            )
            user = cur.fetchone()
        if not user:
            return '', 403
        return view_func(*args, **kwargs, user=user)
    return wrapper
