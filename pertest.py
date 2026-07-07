import sqlite3
from tkinter import *
from tkinter import ttk


con = sqlite3.connect("test2.db")
cur = con.cursor()
# cur.execute("CREATE TABLE movie(title, year, score)")
# res = cur.execute("SELECT name FROM sqlite_master")
# print(res.fetchone())
def exec():
    cur.execute("""
        INSERT INTO movie VALUES
            ('Monty Python and the Holy Grail', 1975, 8.2),
            ('And Now for Something Completely Different', 1971, 7.5)
    """)
    con.commit()


res = cur.execute("SELECT score FROM movie")

root = Tk()
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text=res.fetchall()).grid(column=0, row=0)
ttk.Button(frm, text="Add data", command=exec).grid(column=1, row=0)
root.mainloop()
