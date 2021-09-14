from abc import ABC, abstractmethod

class CleanBay:
	class AbstractPlugin(ABC):
		def verify_cbplugin(self):
			pass

		def verify_status(self):
			pass

		def search(self):
			pass

		def info(self):
			pass