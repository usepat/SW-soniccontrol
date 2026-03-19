from flask import Flask
import abc
from soniccontrol.plugin_discovery import discover_plugins

class ServerPlugin:
    @abc.abstractmethod
    def setup_plugin(self, app: Flask): 
        """
        A plugin should register a blueprint that contains all necessary endpoints. 
        Also provide a url_prefix, to avoid naming collisions.
        """
        ...

def register_server_plugins(app: Flask):
    group= "soniccontrol.server_plugins"

    for plugin in discover_plugins(group):
        plugin.setup_plugin(app)
