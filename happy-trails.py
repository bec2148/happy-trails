from flask import Flask,render_template, request, flash, redirect, url_for
# ...
# https://hevodata.com/learn/flask-mysql/
from flask_mysqldb import MySQL
from pattern.text.en import singularize
import re

# feather icons personalized
DELETE_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-x-circle"><circle cx="12" cy="12" r="10" color="##00FF00"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
EDIT_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="24" viewBox="0 0 24 24" fill="#f3cc76" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-edit-2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>'

regex_id = re.compile(r"Id$")

app = Flask(__name__)

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'my-secret-pw'
app.config['MYSQL_DB'] = 'flask'
mysql = MySQL(app)

def entitle(str):
    title = str.title().replace("_"," ")
    return regex_id.sub("ID", title)

def delete(table, id):
    print("About to delete!!!!")
    cursor = mysql.connection.cursor()
    query = (f"DELETE FROM flask.{table} WHERE id = {id};")
    cursor.execute(query)    
    mysql.connection.commit()
    cursor.close()
    print("about to redirect!!!!!")
    return redirect("/students")

def list(table, can_insert):
    cursor = mysql.connection.cursor()
    query = (f"SELECT * FROM flask.{table};")
    cursor.execute(query)
    # cursor.description  (('id', 8, 2, 20, 20, 0, 0), ('first_name', 253, 11, 300, 300, 0, 1), ('last_name', 253, 13, 300, 300, 0, 1)
    editable = True if cursor.description[0][0].lower() == "id" else False
    headers = ""
    for field in cursor.description:
        column_title = field[0].title().replace("_"," ")
        column_title = regex_id.sub("ID", column_title)
        headers += f"<th>{column_title}</th>"
    if editable:
        headers += "<th></th>"
    rows = ""
    for fields in cursor:
        id = None
        rows += "<tr>"
        for field in fields:
            id = field if id is None else id
            rows += f"<td>{field}</td>"
        href = f"/{table}/{id}/delete"
        if editable:
            rows += f"<td>{EDIT_ICON} <a href=\"{href}\">{DELETE_ICON}</a></tc></tr>"
    cursor.close()
    # https://stackoverflow.com/questions/31387905/converting-plural-to-singular-in-a-text-file-with-python
    singular_table = singularize(table)

    return render_template("table.html", table_title=table.title(), table=table,  headers=headers, rows=rows, can_insert=can_insert, singular_table=singular_table)

def new_record_form(table):
    cursor = mysql.connection.cursor()
    select_columns = f"""
    SELECT column_name, data_type, is_nullable, character_maximum_length
    FROM   information_schema.columns
    WHERE  table_schema = 'flask' AND table_name = '{table}';"""
    cursor.execute(select_columns)
    inputs = ""
    for row in cursor:
        print (f"row {row}")
        if row[0].lower() == 'id':
            continue
        column_name = row[0]
        data_type = row[1]
        print(f"column_name {column_name}  data_type {data_type}")
        inputs += f'<label for="{column_name}">{entitle(column_name)}:</label><br>'
        inputs += f'<input id="{column_name}" name="{column_name}" type="text"><br><br>'
    cursor.close()
    return render_template("new.html", table=table, table_title=entitle(singularize(table)), inputs=inputs)

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
# https://guides.rubyonrails.org/routing.html#crud-verbs-and-actions
@app.route('/<first>', methods = ['POST', 'GET'])
@app.route('/<first>/<path:rest>', methods = ['POST', 'GET'])
def fallback(first=None, rest=None):
    print(f"first {first}  rest {rest}  request.method=='POST' {request.method=='POST'}")
    if rest is None:
        return list(first, can_insert=True)
    if rest == "new":
        return new_record_form(first)
    if rest == "create" and request.method == 'POST':
        return create(first, request.form)
    if rest[-6:].lower() == "delete":
        id = int(rest[:-7])
        return delete(first, id)
