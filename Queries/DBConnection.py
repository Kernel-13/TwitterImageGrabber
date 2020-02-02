import sqlite3

class database():

	def __init__(self, database_name='..\\TwitterMediaGrabber.db'):
		self.conn = sqlite3.connect(database_name)
		self.cursor = self.conn.cursor()

	def close(self):
		self.conn.close()

	def query(self, statement, values=None, fetchall=False, fetchone=False, commit=False):
		if values: self.cursor.execute(statement, values)
		else:	self.cursor.execute(statement)

		if fetchall: 	return self.cursor.fetchall()
		elif fetchone:	return self.cursor.fetchone()
		elif commit: 	self.conn.commit()