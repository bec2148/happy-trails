from flask import Flask,render_template, request
# https://hevodata.com/learn/flask-mysql/
from flask_mysqldb import MySQL
import re

regex_id = re.compile(r"Id$")

app = Flask(__name__)

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'my-secret-pw'
app.config['MYSQL_DB'] = 'flask'
mysql = MySQL(app)

@app.route("/")
def welcome():
    return render_template("welcome.html", message="Students.")

@app.route("/students")
def students():
    #Creating a connection cursor
    cursor = mysql.connection.cursor()
    query = ("SELECT * from flask.students;")
    cursor.execute(query)
    print("cursor.description ", cursor.description)
    headers = ""
    for field in cursor.description:
        column_title = field[0].title().replace("_"," ")
        column_title = regex_id.sub("ID", column_title)
        headers += f"<th>{column_title}</th>"
    rows = ""
    for fields in cursor:
        rows += "<tr>"
        for field in fields:
            rows += f"<td>{field}</td>"
        rows += "</tr>"
    cursor.close()

    return render_template("table.html", table="Students", headers=headers, rows=rows)

# https://stackoverflow.com/questions/14023864/flask-url-route-route-all-other-urls-to-some-function
# under construction:  pull table name from url
@app.route('/<first>', methods = ['POST', 'GET'])
@app.route('/<first>/<path:rest>', methods = ['POST', 'GET'])
def fallback(first=None, rest=None):
    print(f'first {first} rest {rest}')
    cursor = mysql.connection.cursor()
    query = (f"SELECT * from flask.{first};")
