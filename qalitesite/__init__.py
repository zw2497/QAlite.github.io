import os
import jwt
from flask import Flask,g,request
from flask import jsonify



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    @app.before_request
    def before_request():
        try:
            g.conn = db.conn(db.create())
        except:
            g.conn = None

    @app.teardown_request
    def teardown_request(exception):
        try:
            db.disconn(g.conn)
        except Exception as e:
            pass


    @app.route('/', methods=['POST', 'GET'])
    def classinfo():
        db = g.conn

        # result = g.conn.execute("select * from users").fetchall()
        # p = {}
        # for i, j in enumerate(result):
        #     p[i] = j['name']

        # p = "INSERT INTO users (email, password, name) VALUES (%s, %s, %s)"
        # result = db.execute(p, ("zw2497@columbia.edu", "123456", "wzc"))

        p = "SELECT name FROM users WHERE email = %s"
        result = db.execute(p, ("zw2497@columbia.edu")).fetchone()
        return jsonify(body=result['name'])


    @app.route('/register', methods=['POST', 'GET'])
    def register():
        if request.method == 'POST':
            email = request.json['email']
            password = request.json['password']
            name = request.json['name']

            if (not email or not password):
                return jsonify(body="Email or password is incorrect", code=0)

            db = g.conn

            error = None

            """
            check if the user is exist
            """
            p = "SELECT e FROM users WHERE email = %s"
            result = db.execute(p,(email)).fetchone()

            if result is not None:
                error = 'User: {} is already registered.'.format(email)
                return jsonify(body=error, code=0)

            """
            insert user
            """
            if error is None:
                p = "INSERT INTO users (email, password, name) VALUES (%s, %s, %s)"
                result = db.execute(p, (email, password, name))

            return jsonify(body="success login", code=1)

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            email = request.json['email']
            password = request.json['password']

            """
            check null
            """
            if (not email or not password):
                return jsonify(body="Email or password is incorrect", code=0)

            """
            check password
            """
            db = g.conn

            p = "SELECT * FROM users WHERE email = %s"
            result = db.execute(p, (email)).fetchone()

            if password == result['password']:
                try:
                    payload = {
                        'u_id': result['u_id'],
                        'email': result['email']
                    }

                    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
                except Exception as e:
                    return jsonify(status=401, msg="invalid", code=0)

                """
                login success, return token
                """
                return jsonify(token=str(token), code=1)

            """
            return error
            """
            return jsonify(body="Email or password is incorrect", code=0)


    @app.route('/class')
    def course():
        # token = request.headers.get('credentials')
        # try:
        #     payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
        # except:
        #     return jsonify(status=401, msg="invalid access", code=0)
        # else:
        #     u_id = payload["u_id"]
        #     email = payload["email"]
        db = g.conn

        u_id = 3
        p = "SELECT o.o_id, o.name as o_name, o.create_time, u.name as creator  " \
            "FROM enroll e INNER JOIN organizations_create o " \
            "ON e.org_id = o.o_id " \
            "INNER JOIN users u ON o.creator_id = u.u_id " \
            "where e.user_id = %s;"
        res= {}
        result = db.execute(p, (u_id)).fetchall()
        for i, j in enumerate(result):
            res[i] = {}
            res[i]['o_name'] = j['o_name']
            res[i]['create_time'] = j['create_time']
            res[i]['creator'] = j['creator']
        return jsonify(course=res)

    @app.route('/question/content')
    def question():
        db = g.conn
        o_id = request.args.get('o_id')
        """
        attr from request
        """


        p = "SELECT * FROM question_belong_ask WHERE org_id = %s ORDER BY create_time DESC;"
        res = {}
        result = db.execute(p, (o_id)).fetchall()
        for i, j in enumerate(result):
            res[i] = {}
            res[i]['q_id'] = j['q_id']
            res[i]['creator_id'] = j['creator_id']
            res[i]['create_time'] = j['create_time']
            res[i]['solved_type'] = j['solved_type']
            res[i]['public_type'] = j['public_type']
            res[i]['views'] = j['views']
            res[i]['title'] = j['title']
            res[i]['content'] = j['content']
            res[i]['update_time'] = j['update_time']
            res[i]['pin'] = j['pin']
            res[i]['tag_id'] = j['tag_id']
            res[i]['q_type'] = j['q_type']
        return jsonify(question=res)

    @app.route('/comment/content')
    def comment():
        db = g.conn
        """
        attr from request
        # """
        # o_id = request.args.get('o_id')
        # q_id = request.args.get('q_id')
        o_id = 1
        q_id = 4

        p = "select cs.c_id as cs_id, ct.c_id as ct_id, cs.content as cs_content, ct.content as ct_content " \
            "from comments cs  " \
            "left outer join reply r " \
            "on cs.c_id = r.target " \
            "left outer join comments ct " \
            "on r.source = ct.c_id " \
            "where cs.org_id = %s and cs.q_id = %s"

        res = {}
        result = db.execute(p, (o_id, q_id)).fetchall()
        res = [dict(r) for r in result]

        return jsonify(comment=res)

    @app.route('/hello')
    def hello():
        return "hello world"

    return app



