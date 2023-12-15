from flask import Flask,render_template, request, flash, redirect, send_from_directory
# https://hevodata.com/learn/flask-mysql/
from flask_mysqldb import MySQL
from pattern.text.en import singularize
import os
import re

# feather icons personalized
DELETE_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-x-circle"><circle cx="12" cy="12" r="10" color="##00FF00"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
EDIT_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="24" viewBox="0 0 24 24" fill="#ffcc46" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-edit-2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>'

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
    cursor = mysql.connection.cursor()
    query = (f"DELETE FROM flask.{table} WHERE id = {id};")
    cursor.execute(query)
    mysql.connection.commit()
    cursor.close()
    return redirect(f"/{table}")

def name_sql_from_table(table_name):
    """Generate the SQL to request a name field from table table_name

    Args:
        table_name: the number to get the square root of.
    Returns:
        SQL to query the name field (if any) from table table_name.
            Or empty string if no relevant name field exists.
    """
    cursor = mysql.connection.cursor()
    query = """SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'flask' AND table_name = '{table_name}' AND Lower(column_name) LIKE '%name%';
                """
    print(f"query [{query}]")
    cursor.execute(query)
    if len(cursor.description) == 0:
        return ""
    singular_table = singularize(table_name)
    try:
        iname = (i for i,v in enumerate(cursor.description) if v[0].lower() == 'name')
        return f", {table_name}.name as \"{singular_table}_name\" "
    except StopIteration:
        pass
    column_names = cursor.fetchall()
    table_column_names = list(map(lambda column_name: f"{table_name}.{column_name}", column_names))
    cursor.close()
    name_columns = ", ".join(table_column_names)
    return f", concat({name_columns}) as \"{singular_table}_name\" "

def html_from_query(query):
    cursor = mysql.connection.cursor()
    print(f"query [{query}]")
    cursor.execute(query)
    headers = ""
    for field in cursor.description:
        column_title = field[0].title().replace("_"," ")
        column_title = regex_id.sub("ID", column_title)
        headers += f"<th>{column_title}</th>"
    rows = ""
    for fields in cursor:
        id = None
        rows += "<tr>"
        for field in fields:
            id = field if id is None else id
            rows += f"<td>{field}</td>"
    cursor.close()
    return (headers, rows)

def multi_list(table, id):
    """ display multiple tables for the item of id <id> of table <table>
    """
    cursor = mysql.connection.cursor()
    query = (f"SELECT * FROM flask.{table} WHERE id = {id};")
    print(f"query [{query}]")
    cursor.execute(query)
    headers = ""
    for field in cursor.description:
        column_title = field[0].title().replace("_"," ")
        column_title = regex_id.sub("ID", column_title)
        headers += f"<th>{column_title}</th>"
    rows = ""
    for fields in cursor:
        id = None
        rows += "<tr>"
        for field in fields:
            id = field if id is None else id
            rows += f"<td>{field}</td>"
    cursor.close()
    singular_table = singularize(table)
    table_titles=[entitle(table)]
    tables = [table]
    headersz = [headers]
    rowsz = [rows]
    cursor = mysql.connection.cursor()
    query = (f"SELECT table_name FROM information_schema.views WHERE table_schema='flask' AND table_name like '%{table}%';")
    print(f"query [{query}]")
    cursor.execute(query)
    view_names_recordset = cursor.fetchall()
    cursor.close()
    list_tuples_view_names = [*view_names_recordset]
    view_names = [x[0] for x in list_tuples_view_names]
    print (list_tuples_view_names, view_names)
    for view_name in view_names:
        query = (f"SELECT * FROM flask.{view_name} WHERE {singular_table}_id = {id};")
        headers, rows = html_from_query(query)
        table_titles.append(entitle(view_name))
        tables.append(view_name)
        headersz.append(headers)
        rowsz.append(rows)

    # iterate through tables that have a foreign key to this table.
    # ALSO:  includes where *that* table has a foreign key to *another* table
    # If FK2 is popoulated, then the table is a join table.
    # if FK2 is null, then it's just a table.
    query = f"""SELECT cu1.table_name, cu1.column_name "FK", cu1.referenced_table_name "FOREIGN_TABLE", cu1.referenced_column_name "FOREIGN_ID",
                    cu2.column_name "FK2", cu2.referenced_table_name "FOREIGN_TABLE2", cu2.referenced_column_name "FOREIGN_ID2"
                FROM   information_schema.key_column_usage cu1
                    LEFT JOIN (SELECT * FROM information_schema.key_column_usage
                                WHERE referenced_table_name IS NOT NULL) cu2
                            ON cu1.table_name = cu2.table_name AND cu1.referenced_table_name <> cu2.referenced_table_name
                WHERE  cu1.table_schema = 'flask' AND cu1.referenced_table_name = '{table}';"""
    print(f"query [{query}]")
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    table_names = []
    fks = []
    foreign_tables = []
    foreign_ids = []
    fk2s = []
    foreign_table2s = []
    foreign_id2s = []
    for fields in cursor:
        print(f"fields {fields}")
        table_names.append(fields[0])
        fks.append(fields[1])
        foreign_tables.append(fields[2])
        foreign_ids.append(fields[3])
        fk2s.append(fields[4])
        foreign_table2s.append(fields[5])
        foreign_id2s.append(fields[6])
    cursor.close()
    for i in range(len(table_names)):
        table_name = table_names[i]
        name_sql = name_sql_from_table(table_name)



    return render_template("tables.html", id=id, page_title=entitle(table), table_titles=table_titles, tables=tables,  headersz=headersz, rowsz=rowsz)

def list(table, can_insert):
    cursor = mysql.connection.cursor()
    query = (f"SELECT * FROM flask.{table};")
    print(f"query [{query}]")
    cursor.execute(query)
    # cursor.description  (('id', 8, 2, 20, 20, 0, 0), ('first_name', 253, 11, 300, 300, 0, 1), ('last_name', 253, 13, 300, 300, 0, 1)
    editable = True if cursor.description[0][0].lower() == "id" else False
    headers = ""
    link_on_id = False
    for idx, field in enumerate(cursor.description):
        column_title = field[0].title().replace("_"," ")
        if idx == 0 and field[0] == "id":
            link_on_id = True
        column_title = regex_id.sub("ID", column_title)
        headers += f"<th>{column_title}</th>"
    if editable:
        headers += "<th></th>"
    rows = ""
    for fields in cursor:
        id = None
        rows += "<tr>"
        for idx, field in enumerate(fields):
            id = field if id is None else id
            if link_on_id and idx == 0:
                rows += f"<td><a href=\"/{table}/{field}/info\">{field}</a></td>"
            else:
                rows += f"<td>{field}</td>"
        href_edit = f"/{table}/{id}/edit"
        href_delete = f"/{table}/{id}/delete"
        if editable:
            rows += f"<td><a href=\"{href_edit}\">{EDIT_ICON}</a> <a href=\"{href_delete}\">{DELETE_ICON}</a></tc></tr>"
    cursor.close()
    # https://stackoverflow.com/questions/31387905/converting-plural-to-singular-in-a-text-file-with-python
    singular_table = singularize(table)
    return render_template("table.html", table_title=table.title(), table=table,  headers=headers, rows=rows, can_insert=editable, singular_table=singular_table)

def edit_record_form(table, id):
    cursor = mysql.connection.cursor()
    select_columns = f"""
    SELECT column_name, data_type, is_nullable, character_maximum_length FROM   information_schema.columns
    WHERE  table_schema = 'flask' AND table_name = '{table}' ORDER BY ORDINAL_POSITION;;"""
    cursor.execute(select_columns)
    inputs = ""
    columns = []
    for row in cursor:
        print (f"row {row}")
        columns.append((row[0], row[1], row[2], row[3]))
    cursor.close()
    cursor = mysql.connection.cursor()
    select_record = f"select * from {table} where id = {id};"
    cursor.execute(select_record)
    inputs = ""
    values = cursor.fetchone()
    for column, value in zip(columns, values):
        print (f"column value  {column} {value} ")
        value = "" if value is None else value
        column_name = column[0].lower()
        readonly = "readonly" if column_name == "id" else ""
        inputs += f'<label for="{column_name}">{entitle(column_name)}:</label><br>'
        inputs += f'<input id="{column_name}" name="{column_name}" type="text" value={value} {readonly}><br><br>'
    action = f"/{table}/{id}/update"
    print ("action {action}")
    return render_template("edit.html", table=table, table_title=entitle(singularize(table)), inputs=inputs, id=id, action=action)

def new_record_form(table):
    cursor = mysql.connection.cursor()
    select_columns = f"""
    SELECT column_name, data_type, is_nullable, character_maximum_length FROM   information_schema.columns
    WHERE  table_schema = 'flask' AND table_name = '{table}' ORDER BY ORDINAL_POSITION;"""
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

def update(table, id, form):
    print(f"form.__class__ {form.__class__}")
    id = form["id"]
    sets = "SET "
    for key, value in form.items():
        if key != "id":
            if len(value) > 0:
                value = value.replace("'", "''")
                sets += f"{key} = '{value}', "
            else:
                sets += f"{key} = NULL, "
    sets = sets[:-2]
    update = f"UPDATE flask.{table} {sets} WHERE ID = {id};"
    print (f"update query [{update}]")
    cursor = mysql.connection.cursor()
    ret = cursor.execute(update)
    print(f"ret {ret}")
    mysql.connection.commit()
    cursor.close()
    return redirect(f"/{table}")

def create(table, form):
    print(f"form {form}")
    columns = []
    values = []
    for key, value in form.items():
        if value is None or len(value) == 0:
            continue
        value = value.replace("'", "''")
        columns.append(key)
        values.append(value)
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
    return redirect(f"/{table}")

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

@app.route('/favicon.ico')
def favicon():
    print (f"app.root_path {app.root_path}   os.path.join(app.root_path, 'static') {os.path.join(app.root_path, 'static')}")
    return send_from_directory(os.path.join(app.root_path, 'static'), 'HappyTrails.ico')

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
    if rest[-6:].lower() == "update" and request.method == 'POST':
        id = int(rest[:-7])
        return update(first, id, request.form)
    if rest[-6:].lower() == "delete":
        id = int(rest[:-7])
        return delete(first, id)
    if rest[-4:].lower() == "edit":
        id = int(rest[:-5])
        return edit_record_form(first, id)
    if rest[-4:].lower() == "info":
        id = int(rest[:-5])
        return multi_list(first, id)
