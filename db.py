import sqlite3


class DB(object):
    def __init__(self):
        self.conn = sqlite3.connect('cache.db')
        self.cur = self.conn.cursor()

    def db_close(self):
        self.cur.close()
        self.conn.close()

    def drop_table(self, table_name):
        sql_statement = "DROP TABLE {}".format(table_name)
        self.conn.execute(sql_statement)

    def create_table(self, table_name, query=None):
        columns = "project_id INTEGER PRIMARY KEY, project_name TEXT, total INTEGER, completed INTEGER"
        sql_statement = "CREATE TABLE IF NOT EXISTS {0} ({1})".format(table_name,columns)
        self.conn.execute(sql_statement)

    def json_to_db(self, json_prjs):
        query = "INSERT INTO projects values (?,?,?,?) "
        columns = ['id','name']        
        for prj in json_prjs:
            if self.cur.execute("SELECT * FROM projects WHERE project_id={}".format(prj['id'])).fetchall():
                continue
            else:
                values = tuple(prj[c] for c in columns) + (0,0)
                self.conn.execute(query, values)
        self.conn.commit()

        # solving if project is deleted in Asana.
        prj_ids = [prj["id"] for prj in json_prjs]
        prj_del_ids = self.cur.execute("SELECT project_id FROM projects WHERE project_id NOT IN {}".format(tuple(prj_ids))).fetchall()
        if prj_del_ids:
            print(">>>>>>>>DELETING {} projects from DB!".format(len(prj_del_ids)))
            self.conn.execute("DELETE FROM projects WHERE project_id NOT IN {}".format(tuple(prj_ids)))
        self.conn.commit()

    def update_project_percentage(self, project_id,total,completed):
        if self.cur.execute("SELECT project_id FROM projects WHERE total={0} and completed={1} and project_id={2}".format(total,completed,project_id)).fetchall():
            return
        print(">>>>>>>UPDATING percentage for project:{}".format(project_id))
        self.conn.execute("UPDATE projects SET total={0},completed={1} WHERE project_id={2}".format(total,completed,project_id))
        self.conn.commit()




if __name__ == '__main__':
    ###### db - cache - BEGIN #####################################################
    db = DB()
    #db.drop_table('projects')
    #db.create_table('projects')
    db.conn.execute("insert into projects values (?,?,?,?) ", (1,'test',0,0))
    db.conn.execute("insert into projects values (?,?,?,?) ", (2,'test2',0,0))
    db.conn.commit()
    ids = [1,2]
    a = db.cur.execute("SELECT * FROM projects WHERE project_id in {}".format(tuple(ids)))
    print(a)
    print(a.fetchall())
    if a.fetchall():
        print("OKKKK")
    db.db_close()
    print("Done DB work!!!")

    ###### db - cache - END #######################################################
