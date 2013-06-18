from flask import Flask
from flask_peewee.db import Database


import ConfigParser
import json

app = None
conf = None
database = None



def create_app(config_path):
	global app, conf, database
	conf = ConfigParser.ConfigParser()
	conf.read([config_path])	

	app =  Flask(__name__, static_folder = conf.get('flask', 'static_folder'), template_folder=conf.get('jinja','template_path'))
	app.config['DATABASE'] = dict(conf.items('database'))
	database = Database(app)
	import server 
	server.init_db()

	return app
