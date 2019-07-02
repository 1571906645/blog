# coding: utf-8
from search import app

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8008, threaded=True)
    # app.run(host='127.0.0.1', port=5555, ssl_context='adhoc',threaded=True)
