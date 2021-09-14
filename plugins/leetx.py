from . import abstract_plugin

class CBPlugin(abstract_plugin.CleanBay.AbstractPlugin):
	def verify_cbplugin(self):
		return True

	def verify_status(self):
		return True

	def search(self):
		return []

	def info(self):
		return {
			'name': 'leetx',
			'back': '1337x.to'
		}