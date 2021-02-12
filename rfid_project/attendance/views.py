import os
import sqlite3

from django.shortcuts import render
from django.http import HttpResponse

import serial
from rfid_project.settings import BASE_DIR
from .models import Client, Log
from django.shortcuts import redirect
import datetime

global stat
stat = ''
# Create your views here.
global selected
selected = None


def index(request):
	return render(request, 'attendance/index.html')

def process(request):
	card = request.GET.get('card_id', 'get nothing')
	users = Client.objects.all()
	for user in users:
		if user.card_id == int(card):
			ans = attend(user)
			return HttpResponse(ans)
	new_user = Client(card_id=int(card))
	new_user.save()
	return HttpResponse('registered successfully')


def attend(user):
	if user.name == None:
		statu = 'Save your profile'
		return statu
	logs = Log.objects.all()
	for log in logs:
		if log.card_id == int(user.card_id):
			if str(log.date) == str(datetime.datetime.now())[:10]:
				if log.time_out == None:
					log.time_out = datetime.datetime.now()
					log.save()
					statu = 'logout'
					return statu
				else:
					statu = 'Get out now'
					return statu
	new_log = Log(ida=user.id, card_id=user.card_id, name=user.name, phone=user.phone, date=datetime.datetime.now(),
				  time_in=datetime.datetime.now(), status='')
	new_log.save()
	statu = 'auth'
	return statu


def details1(request):
	users = Client.objects.all()
	us = []
	for user in users:
		us.append(user)
	us.reverse()
	userset = {'users': us}
	return render(request, 'attendance/userdetails.html', userset)


def details(request):
	return render(request, 'attendance/details.html')


def manage1(request):
	users = Client.objects.all()
	us = []
	for user in users:
		us.append(user)
	us.reverse()
	global stat
	userset = {'users': us}
	stat = ''
	return render(request, 'attendance/allusers.html', userset)


def manage(request):
	global stat
	status = {'cardstatus': stat}
	return render(request, 'attendance/manage.html', status)


def card(request):
	users = Client.objects.all()
	global stat
	global selected
	if request.method == 'POST':
		if request.POST.get("sel"):
			ids = request.POST.get('namesearch', 'get nothing')
			for user in users:
				if user.name == str(ids):
					stat = 'Card is Selected'
					selected = user
					break
				else:
					stat = 'Card not found'
			return redirect('/manage')
		else:
			ids = request.POST.get('namesearch')
			if Client.objects.filter(name=str(ids)).exists():
				Client.objects.filter(name=str(ids)).update(
					name=None, dob=None, phone=None, sex=None, email=None, address=None)
				stat = 'Deleted Successfully'
			else:
				stat = 'Card not found'
			return redirect('/manage')


def edit(request):
	i = 0
	users = Client.objects.all()
	global selected
	global stat
	if selected == None:
		stat = 'No Card was Selected'
		return redirect('/manage')
	else:
		name = request.POST.get('name')
		dob = request.POST.get('date')
		phone = request.POST.get('phone')
		email = request.POST.get('email')
		gender = request.POST.get('gender')
		address = request.POST.get('address')
		new = [name, phone, dob, email, gender, address]
		for user in users:
			if user.card_id == selected.card_id:
				old = [user.name, user.phone, user.dob, user.email, user.sex, user.address]
				for item in new:
					if item == '' or item is None:
						new[i] = old[i]
					i = i + 1
				user.name = new[0]
				user.phone = new[1]
				user.dob = new[2]
				user.email = new[3]
				user.sex = new[4]
				user.address = new[5]
				user.save()
				stat = 'Profile Updated'
		selected = None
		return redirect('/manage')


def search(request):
	sel_user = ''
	users = Client.objects.all()
	logs = Log.objects.all()
	path = request.get_full_path()
	name = request.POST.get('search')
	if (name):
		logf = []
		for user in users:
			if str(user.name) == str(name):
				sel_user = user
		for log in logs:
			if str(log.date)[5:7] == str(datetime.datetime.now())[5:7] and str(log.name) == str(name):
				logf.append(log)
		logf.reverse()
		dataset = {'use': sel_user, 'log': logf}
		return render(request, 'attendance/search.html', dataset)
	else:
		return redirect(request.META['HTTP_REFERER'])



def Arduino_Data(request):
	"""logf = []
	logs = Log.objects.all()
	for log in logs:
		# if str(log.date) == str(datetime.datetime.now())[:10]:
		logf.append(log)
	logf.reverse()
	dataset = {'log': logf}
	return render(request, 'attendance/attendance.html', dataset)"""
	Data_serie = serial.Serial('com10', 9600)
	while(1):
		if (Data_serie.inWaiting() > 0):
			maData = Data_serie.readline()
			pieces = str(maData, encoding='UTF-8')
			print(pieces)
			i = 0
			c = pieces[i]
			t = ""
			while (c != ' '):
				t += pieces[i]
				i += 1
				c = pieces[i]
			id = int(t)
			searchfunc(id)
			logf = []
			logs = Log.objects.all()
			for log in logs:
				# if str(log.date) == str(datetime.datetime.now())[:10]:
				logf.append(log)
			logf.reverse()
			dataset = {'log': logf}
			return render(request, 'attendance/attendance.html', dataset)


def searchfunc(id):
	try:
		sqliteConnection = sqlite3.connect(os.path.join(BASE_DIR, 'db.sqlite3'))
		cursor = sqliteConnection.cursor()
		print("Connected to SQLite")

		sql_select_query = """select * from attendance_client where card_id = ?"""
		cursor.execute(sql_select_query, (id,))
		records = cursor.fetchall()
		for row in records:
			insertBLOB(row[0], row[1], row[2], row[4])
		cursor.close()

	except sqlite3.Error as error:
		print("Failed to read data from sqlite table", error)
	finally:
		if (sqliteConnection):
			sqliteConnection.close()
			print("The SQLite connection is closed")


def insertBLOB(ida, card_id, name, phone):
	try:
		sqliteConnection = sqlite3.connect(os.path.join(BASE_DIR, 'db.sqlite3'))
		cursor = sqliteConnection.cursor()
		print("Connected to SQLite")
		sqlite_insert_blob_query = """ INSERT INTO attendance_log
                                  (id,ida,card_id,name,phone,date,time_out,status,time_in) VALUES (NULL,?,?,?,?,date(),TIME(),"",TIME())"""

		# Convert data into tuple format
		data_tuple = (ida, card_id, name, phone)
		cursor.execute(sqlite_insert_blob_query, data_tuple)
		sqliteConnection.commit()
		print("new log inserted successfully as a BLOB into a table")
		cursor.close()

	except sqlite3.Error as error:
		print("Failed to insert blob data into sqlite table", error)
	finally:
		if (sqliteConnection):
			sqliteConnection.close()
			print("the sqlite connection is closed")

