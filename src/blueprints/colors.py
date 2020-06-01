import sqlite3
from flask import (
    Blueprint,
    jsonify,
    request,
    session
)

from flask.views import MethodView

from src.database import db

bp = Blueprint('colors', __name__)


class ColorsView(MethodView):
    def post(self):
        with db.connection as con:
            cur = con.execute("""
            SELECT id
            FROM seller
            WHERE account_id = ?
            """,
            (session['id'],)
            )
            is_seller = cur.fetchone()
        is_seller = dict(is_seller)
        if not bool(is_seller['id']):
            return '', 403

        request_json = request.json
        name = request_json.get('name')
        hex = request_json.get('hex')
        try:
            with db.connection as con:
                con.execute("""
                    INSERT INTO color (name, hex)
                    VALUES (?, ?)
                """, (name, hex)
                )
                con.commit()
                cur = con.execute("""
                    SELECT *
                    FROM color
                    WHERE name = ?
                """,
                (name,)
                )
                response = cur.fetchone()
            return jsonify(dict(response)), 201
        except sqlite3.IntegrityError:
            with db.connection as con:
                cur = con.execute("""
                    SELECT *
                    FROM color
                    WHERE name = ?
                """,
                (name,)
                )
                response = cur.fetchone()
            return jsonify(dict(response)), 302


bp.add_url_rule('', view_func = ColorsView.as_view('colors'))
