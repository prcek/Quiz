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

	def get_short_desc(self):
		return self.description

	def get_desc(self):
		return self.category.name + " " + self.description

class Answer(BaseModel):
	question = ForeignKeyField(Question, db_index=True,related_name='answers')
	text = TextField()
	correct = BooleanField(default=False)

class ExamTemplate(BaseModel):
	name = CharField()
	max_time = IntegerField()

	def get_edit_url(self):
		return url_for('exam_template_edit',exam_template_id=self.id)

	def get_erase_url(self):
		return url_for('exam_template_erase',exam_template_id=self.id)

	def get_next_no(self):
		m = 0
		for q in self.questions:
			if q.question_no>m:
				m=q.question_no
		return m+1
	def get_questions(self):
		return self.questions.order_by(ExamTemplateQuestion.question_no)


class ExamTemplateQuestion(BaseModel):
	exam_template = ForeignKeyField(ExamTemplate, db_index=True, related_name='questions')
	question_no = IntegerField(db_index=True)
	question = ForeignKeyField(Question,db_index=True)

	class Meta:
		order_by = ("question_no")

	def get_category(self):
		return self.question.category.name

	def get_desc(self):
		return self.question.get_desc()

 


class Exam(BaseModel):
	applicant = TextField()
	exam_template = ForeignKeyField(ExamTemplate, db_index=True, related_name='exams')
	exam_start = DateTimeField()
	exam_stop = DateTimeField()

class ExamAnswer(BaseModel):
	exam = ForeignKeyField(Exam, db_index=True, related_name='answers')
	question = ForeignKeyField(Question, db_index=True)
	answer = ForeignKeyField(Answer, null=True)



ALL_MODELS = [Category,Question,Answer,Exam,ExamAnswer,ExamTemplate, ExamTemplateQuestion]

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


	et1 = ExamTemplate.create(name='examtempl1',max_time=60) 
	et1.save()

	et2 = ExamTemplate.create(name='examtempl2',max_time=125) 
	et2.save()


	etq=ExamTemplateQuestion.create(exam_template=et1, question_no=1, question=q1)
	etq.save()
	etq=ExamTemplateQuestion.create(exam_template=et1, question_no=2, question=q2)
	etq.save()
	etq=ExamTemplateQuestion.create(exam_template=et1, question_no=3, question=q3)
	etq.save()

	etq=ExamTemplateQuestion.create(exam_template=et2, question_no=1, question=q1)
	etq.save()


##### VIEWS #####



@app.route("/")
def view():
    return render_template('index.html', text='hello!')

@app.route("/templates", methods=['GET','POST'])
def exam_templates():
	if request.method == 'POST':
		t = ExamTemplate.create(name=request.form['desc'],max_time=request.form['max']);
		t.save()
		return redirect(url_for('exam_template_edit',exam_template_id=t.id))
	data = {
		"list":ExamTemplate.select()
	}
	return render_template('templates.html',**data)

@app.route("/templates/<int:exam_template_id>", methods=['GET', 'POST'])
def exam_template_edit(exam_template_id):
	if request.method == 'POST':
		if request.form['action'] == 'D':
			t = ExamTemplate.get(id=exam_template_id)
			t.name = request.form['desc']
			t.max_time = request.form['max']
			t.save()
		if request.form['action'] == 'A':
			t = ExamTemplate.get(id=exam_template_id)
			q = Question.get(id=request.form['qid'])
			ti = ExamTemplateQuestion.create(exam_template=t, question_no=request.form['q_no'],question=q)
			ti.save()
			return redirect(url_for('exam_template_edit', exam_template_id=t.id))

		if request.form['action'] == 'O':
			t = ExamTemplate.get(id=exam_template_id)
			for k in request.form.keys():
				if k[0:4]=="qid_":
					id = k[4:]
					etq = ExamTemplateQuestion.get(id=id)
					etq.question_no = request.form[k]
					etq.save()

			return redirect(url_for('exam_template_edit', exam_template_id=t.id))


		if request.form['action'] == 'OC':
			t = ExamTemplate.get(id=exam_template_id)
			no = 1
			for etq in t.questions.order_by(ExamTemplateQuestion.question_no):
					etq.question_no = no
					etq.save()
					no = no + 1

			return redirect(url_for('exam_template_edit', exam_template_id=t.id))


		if request.form['action'] == 'DQ':
			t = ExamTemplate.get(id=exam_template_id)

			for i in request.form.getlist('q_check'):
				etq = ExamTemplateQuestion.get(id=i)
				etq.delete_instance()

			return redirect(url_for('exam_template_edit', exam_template_id=t.id))


	data = {
		"t": ExamTemplate.get(id=exam_template_id),
		"all_questions": Question.select()
	}
	return render_template('template_edit.html',**data)

@app.route("/templates/erase/<int:exam_template_id>")
def exam_template_erase(exam_template_id):
	t =  ExamTemplate.get(id=exam_template_id)
	t.delete_instance()
	return redirect(url_for('exam_templates'))


@app.route("/q/<int:question_id>", methods=['GET', 'POST'])
def question(question_id):

	if request.method == 'POST':
		print request.form
		next = question_id+1
		if next>6:
			next=1
		return redirect(url_for('question',question_id=next))


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

