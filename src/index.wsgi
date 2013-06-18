#!/usr/bin/env python
# encoding:utf8

from index import create_app

app_instance = None

def application(environ, start_response):
	global  app_instance
	if app_instance is None:
		app_instance = create_app(environ["configFile"])

	return app_instance(environ, start_response)


if __name__ == "__main__":
	app_instance = create_app("conf/quiz.conf")
	app_instance.run(host='0.0.0.0',debug=True)
