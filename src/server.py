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
import os

from index import app
from index import database

from peewee import *


##### MODELS #####

class BaseModel(database.Model):
    pass

class Category(BaseModel):
	name =  CharField()

	def is_empty(self):
		return len([t for t in self.questions])==0
	def get_edit_url(self):
		return url_for('category_edit',category_id=self.id)
	def get_questions_table_url(self):
		return url_for('questions', category_id=self.id)


class Question(BaseModel):
	category = ForeignKeyField(Category,db_index=True,related_name='questions')
	description = TextField()

	def is_used_in_template(self):
		return len([t for t in self.templates])>0

	def get_preview_url(self):
		return url_for('question_preview',question_id=self.id)

	def get_edit_url(self):
		return url_for('question_edit',question_id=self.id)
	def get_questions_table_url(self):
		return url_for('questions', category_id=self.category.id)

	def get_short_desc(self):
		return self.description

	def get_desc(self):
		return self.category.name + " " + self.description

class Answer(BaseModel):
	question = ForeignKeyField(Question, db_index=True,related_name='answers')
	text = TextField()
	correct = BooleanField(default=False)

	def get_desc(self):
		return self.text

class ExamTemplate(BaseModel):
	name = CharField()
	max_time = IntegerField()

	def get_exam_create_url(self):
		return url_for('exam_create', exam_template_id=self.id)

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
	question = ForeignKeyField(Question,db_index=True, related_name='templates')

	class Meta:
		order_by = ("question_no")

	def get_category(self):
		return self.question.category.name

	def get_desc(self):
		return self.question.get_desc()

 


class Exam(BaseModel):
	exam_template = ForeignKeyField(ExamTemplate, db_index=True, related_name='exams')
	shash = CharField(db_index=True)
	applicant = TextField()
	exam_created = DateTimeField(default=datetime.datetime.now)
	exam_start = DateTimeField(null=True)
	exam_stop = DateTimeField(null=True)
	last_answer_time = DateTimeField(null=True)
	cursor = IntegerField()
	closed = BooleanField(default=False)
	question_count = IntegerField(null=True)
	question_correct = IntegerField(null=True)
	question_wrong = IntegerField(null=True)

	def get_date(self):
		return self.exam_created.strftime("%Y-%m-%d %H:%M")

	def get_key(self):
		return self.shash+"_"+self.id

	def get_result(self):
		return "%d/%d" % (self.question_correct,self.question_count)

	def get_detail_url(self):
		return url_for('exam_detail',exam_id=self.id)


class ExamAnswer(BaseModel):
	no = IntegerField()
	exam = ForeignKeyField(Exam, db_index=True, related_name='answers')
	question = ForeignKeyField(Question, db_index=True)
	answer = ForeignKeyField(Answer, null=True)
	question_text = TextField()
	answer_text = TextField()
	answer_correct = BooleanField(default=False)



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
	data = {
		"exam_templates":ExamTemplate.select(),
	}
	return render_template('index.html', **data)

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
			return redirect(url_for('exam_templates'))
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


@app.route("/questions")
@app.route("/questions/<int:category_id>", methods=['GET','POST'])
def questions(category_id=None):
	if category_id == None:
		return redirect(url_for('questions', category_id=Category.get().id))

	if request.method == 'POST':
		if request.form['action'] == 'NC':
			return redirect(url_for('questions', category_id=request.form['new_cat']))
		if request.form['action'] == 'NQ':
			category = Category.get(id=category_id)
			q=Question.create(category=category)
			q.save()
			return redirect(url_for('question_edit',question_id=q.id))


	category = Category.get(id=category_id)

	data = {
		"category": category,
		"categories": Category.select(),
		"questions": category.questions,
	}


	return render_template('questions.html',**data)

@app.route("/question/<int:question_id>", methods=["GET","POST"])
def question_edit(question_id):

	question = Question.get(id=question_id)
	alert = None

	if request.method == 'POST':
		if request.form['action']=='A':
			question.description = request.form['desc']
			question.save()
			a = Answer.create(question=question)
			a.save()
		if request.form['action']=='S':
			question.description = request.form['desc']
			question.save()
			correct_id = request.form['ansRadios']
			for k in request.form.keys():
				if k[0:2]=="a_":
					id = k[2:]
					val = request.form[k]
					cor = id == correct_id
					ans = Answer.get(id = id)
					if val == '':
						ans.delete_instance()
					else:
						ans.correct=cor
						ans.text=val
						ans.save()
		if request.form['action']=='D':
			if question.is_used_in_template():
				alert = u"Nelze smazat, otázka je použitá v sabloně"
			else:
				question.delete_instance()
				return redirect(url_for('questions', category_id=question.category.id))									

	data = {
		"alert":alert,
		"q": question,
	}
	return render_template('question_edit.html',**data)


@app.route("/categories",methods=['POST','GET'])
def categories():
	if request.method == 'POST':
		if request.form['action']=='NC':
			c = Category.create()
			c.save()
			return redirect(url_for('category_edit',category_id=c.id))

	data = {
		"categories": Category.select()
	}
	return render_template('categories.html', **data)

@app.route("/category/<int:category_id>",methods=['POST','GET'])
def category_edit(category_id):
	alert = None
	cat = Category.get(id=category_id)

	if request.method == "POST":
		if request.form['action']=='S':
			cat.name = request.form['cat_name']
			cat.save()
			return redirect(url_for('categories'))
		if request.form['action']=='D':
			if cat.is_empty():
				cat.delete_instance()
				return redirect(url_for('categories'))
			else:
				alert = u'Nelze smazat, kategorie není prázdná'


	data = {
		"alert": alert,
		"category": cat
	}
	return render_template('category_edit.html', **data)

@app.route("/exams")
def exam_list():
	data = {
		"exams": Exam.select().order_by(-Exam.exam_created),
	}
	return render_template('exams.html',**data)

@app.route("/exam/<int:exam_id>")
def exam_detail(exam_id):
	return ""

@app.route("/exam_create/<int:exam_template_id>", methods=['GET', 'POST'])
def exam_create(exam_template_id):



	et = ExamTemplate.get(id = exam_template_id)

	if request.method == 'POST':
		ex = Exam.create(exam_template=exam_template_id)
		ex.applicant = request.form['applicant']
		ex.exam_created = datetime.datetime.now()
		ex.cursor = 0
		ex.save()
		ex.shash = os.urandom(16).encode('hex')+"_%d" % ex.id
		ex.save()


		no = 0
		for qi in et.get_questions():
			no+=1
			ea = ExamAnswer(exam=ex,question=qi.question,no=no)
			ea.save()

		ex.question_count = no
		ex.question_correct = 0
		ex.question_wrong = 0
		ex.save()


		return redirect(url_for('exam_start',exam_shash=ex.shash))

	data = {
		"et":et,
	}


	return render_template('exam_create.html',**data)


@app.route("/exam_start/<exam_shash>")
def exam_start(exam_shash):
	e = Exam.get(shash=exam_shash)
	data = {
		"e": e,
	}
	return render_template('exam_start.html',**data)





@app.route("/q_preview/<int:question_id>", methods=['GET', 'POST'])
def question_preview(question_id):

#	if request.method == 'POST':
#		print request.form
#		next = question_id+1
#		if next>6:
#			next=1
#		return redirect(url_for('question',question_id=next))


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




