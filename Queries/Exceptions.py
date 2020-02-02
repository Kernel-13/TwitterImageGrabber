class TwitterMediaGrabberError(Exception):
	def __init__(self, message):
		self.message = message

	def __str__(self):
		return '### ERROR ### - {}'.format(self.message)
		
class InvalidName(TwitterMediaGrabberException):	pass
class UserExists(TwitterMediaGrabberException):		pass
class FolderExists(TwitterMediaGrabberException):	pass
class UnknownUser(TwitterMediaGrabberException):	pass
class UnknownStatus(TwitterMediaGrabberException):	pass
