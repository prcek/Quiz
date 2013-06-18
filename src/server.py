#!/usr/bin/env python
# encoding:utf8
from flask import Flask, url_for, render_template, abort, redirect, make_response, send_file, request
import hashlib
import datetime
from cStringIO import StringIO
import random
from flask_peewee.db import Database, R
from wtfpeewee.orm import model_form
import wtforms
import getpass
import json
import urllib

from index import app
from index import database

from peewee import *


##### MODELS #####

class BaseModel(database.Model):
    pass

class Question(BaseModel):
	description = TextField(null=True)



ALL_MODELS = [Question]

def init_db():
    for m in ALL_MODELS:
        m.create_table(fail_silently=True)


##### VIEWS #####

@app.route("/")
def view():
    return render_template('index.html', text='hello!')



