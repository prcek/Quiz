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

class Category(BaseModel):
	name =  CharField()

class Question(BaseModel):
	category = ForeignKeyField(Category,db_index=True,related_name='questions')
	description = TextField()

class Answer(BaseModel):
	question = ForeignKeyField(Question, db_index=True,related_name='answers')
	text = TextField()
	correct = BooleanField(default=False)

class Exam(BaseModel):
	applicant = TextField()
	exam_start = DateTimeField()
	exam_stop = DateTimeField()

class ExamAnswer(BaseModel):
	exam = ForeignKeyField(Exam, db_index=True, related_name='answers')
	question = ForeignKeyField(Question, db_index=True)
	answer = ForeignKeyField(Answer, null=True)



ALL_MODELS = [Category,Question,Answer,Exam,ExamAnswer]

def init_db():
    for m in ALL_MODELS:
        m.create_table(fail_silently=True)

def load_db():
	kat1 = Category.create(name='Kat1')
	kat1.save()
	kat2 =  Category.create(name='Kat2')
	kat2.save()

	q1 = Question.create(description='q1',category=kat1)
	q1.save()

	q2 = Question.create(description='q2',category=kat1)
	q2.save()

	q3 = Question.create(description='q3',category=kat2)
	q3.save()


	a1q1 = Answer.create(question=q1,text='a1q1',correct=False)
	a1q1.save()

	a2q1 = Answer.create(question=q1,text='a2q1',correct=False)
	a2q1.save()

	a3q1 = Answer.create(question=q1,text='a3q1',correct=True)
	a3q1.save()

	a1q2 = Answer.create(question=q2,text='a1q2',correct=False)
	a1q2.save()

	a2q2 = Answer.create(question=q2,text='a2q2',correct=False)
	a2q2.save()

	a3q2 = Answer.create(question=q2,text='a3q2',correct=True)
	a3q2.save()

	a1q3 = Answer.create(question=q3,text='a1q3',correct=False)
	a1q3.save()

	a2q3 = Answer.create(question=q3,text='a2q3',correct=True)
	a2q3.save()


	pass        


##### VIEWS #####

@app.route("/")
def view():
    return render_template('index.html', text='hello!')

@app.route("/q/<int:question_id>")
def question(question_id):
	question = Question.get(id=question_id)
	
	q_no = 3
	q_total = 20
	t_total = "00:06:10"
	t_left  = 10

	data = {
		"q":question,
		"q_no":q_no,
		"q_total":q_total,
		"t_total":t_total,
		"t_left":t_left,
	}
	return render_template('question.html', **data)

