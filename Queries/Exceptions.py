import logging

class TwitterMediaGrabberError(Exception):
	def __init__(self, message):
		self.message = message

	def __repr__(self):
		logging.error(message)
		return "\t\t\t### ERROR ### - {}".format(self.message)
		
class InvalidName(TwitterMediaGrabberError):		pass
class UserExists(TwitterMediaGrabberError):			pass
class FolderExists(TwitterMediaGrabberError):		pass
class UnknownUser(TwitterMediaGrabberError):		pass
class UnknownStatus(TwitterMediaGrabberError):		pass
class MaxDupesFound(TwitterMediaGrabberError):		pass
class MaxTweetsFetched(TwitterMediaGrabberError):	pass

def print_error(message):
	logging.error(message)
	print("\t\t\t### ERROR ### - {}".format(message))

def print_warning(message):
	logging.warning(message)
	print("\t\t{}".format(message))

def print_info(message):
	logging.info(message)
	print("\t{}".format(message))