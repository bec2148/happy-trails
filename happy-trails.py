from flask import Flask,render_template, request, flash, redirect, url_for
# ...
# https://hevodata.com/learn/flask-mysql/
from flask_mysqldb import MySQL
from pattern.text.en import singularize
import re

regex_id = re.compile(r"Id$")

app = Flask(__name__)

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'my-secret-pw'
app.config['MYSQL_DB'] = 'flask'
mysql = MySQL(app)

def list(table, can_insert):
    cursor = mysql.connection.cursor()
    query = (f"SELECT * from flask.{table};")
    cursor.execute(query)
    # cursor.description  (('id', 8, 2, 20, 20, 0, 0), ('first_name', 253, 11, 300, 300, 0, 1), ('last_name', 253, 13, 300, 300, 0, 1)
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
    # https://stackoverflow.com/questions/31387905/converting-plural-to-singular-in-a-text-file-with-python
    singular_table = singularize(table)
    print("can_insert ", can_insert)

    return render_template("table.html", table_title=table.title(), table=table,  headers=headers, rows=rows, can_insert=can_insert, singular_table=singular_table)

def create(table, form):
    print(f"form {form}")

    columns = form.keys()
    values = form.values()
    print(f"columns {columns}  values {values}")
    columns_str = ",".join(columns)
    values_str = "'" + "','".join(values) + "'"
    insert = f"INSERT INTO flask.{table} ({columns_str}) VALUES ({values_str})"
    print (f"insert query {insert}")
    cursor = mysql.connection.cursor()
    ret = cursor.execute(insert)
    print(f"ret {ret}")
    mysql.connection.commit()
    cursor.close()
    return redirect("/students")

@app.route("/")
def welcome():
    cursor = mysql.connection.cursor()
    query = ("SELECT table_name from information_schema.tables WHERE table_schema='flask';")
    cursor.execute(query)
    headers = ""
    for field in cursor.description:
        column_title = field[0].title().replace("_"," ")
        column_title = regex_id.sub("ID", column_title)
        headers += f"<th>{column_title}</th>"
    rows = ""
    for fields in cursor:
        rows += "<tr>"
        for field in fields:
            rows += f"<td><a href=\"/{field}\">{field}</a></td>"
        rows += "</tr>"
    cursor.close()
    return render_template("table.html", table_title="Tables", headers=headers, rows=rows)

# https://stackoverflow.com/questions/14023864/flask-url-route-route-all-other-urls-to-some-function
# under construction:  pull table name from url
@app.route('/<first>', methods = ['POST', 'GET'])
@app.route('/<first>/<path:rest>', methods = ['POST', 'GET'])
def fallback(first=None, rest=None):
    print(f"first {first}  rest {rest}  request.method=='POST' {request.method=='POST'}")
    if rest is None:
        return list(first, can_insert=True)
    if rest == "new":
        return render_template("new.html", table=first)
    if rest == "create" and request.method == 'POST':
        return create(first, request.form)


