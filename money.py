#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import sys
import getopt
import time
from datetime import datetime

print('\n####################################################')
print('#############  Simple Finance Tool v0.1  ###########')
print('#############        zach@2018           ###########')
print('####################################################')

print('\n--查看show、退出q、分类cat、账户account')
print('查看指定账户: show 1 、切换账户: account [账户编号]、新建账户: account [账户名称]')
print('输入格式:-100 0 [备注信息]')


def db_filepath():
	return os.path.join(os.path.dirname(__file__), 'finance2.db')

def setup_db():
	db_file = db_filepath()
	if not os.path.isfile(db_file):
		print('create table...')
		conn = sqlite3.connect(db_file)
		cursor = conn.cursor()
		cursor.execute('create table records(id INTEGER PRIMARY KEY AUTOINCREMENT, money NUMERIC NOT NULL, cat INTEGER(5) NOT NULL, account INTEGER(5) NOT NULL, note VARCHAR(50), time DATETIME(20) NOT NULL)')
		cursor.execute('create table cats(id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(20) NOT NULL)')
		cursor.execute('create table accounts(id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(20) NOT NULL)')
		cursor.execute('insert into accounts(name) values (\'现金账户\')')
		cursor.execute('insert into accounts(name) values (\'支付宝账户\')')
		cursor.execute('insert into accounts(name) values (\'信用卡账户\')')
		cursor.close()
		conn.commit()
		conn.close()

def check_exist(sql):
	conn = sqlite3.connect(db_filepath())
	cursor = conn.cursor()
	cursor.execute(sql)
	results = cursor.fetchall()
	cursor.close()
	conn.close()
	return len(results) > 0

def query_matches(sql):
	conn = sqlite3.connect(db_filepath())
	cursor = conn.cursor()
	cursor.execute(sql)
	results = cursor.fetchall()
	cursor.close()
	conn.close()
	return results

def insert_db(sql):
	conn = sqlite3.connect(db_filepath())
	cursor = conn.cursor()
	result = cursor.execute(sql)
	cursor.close()
	conn.commit()
	conn.close()
	return result

def show_accounts():
	output = '--账户：'
	for account in query_matches("select * from accounts"):
		output += str(account[0]) + '-' + account[1] + '  '
	print(output+'\n')


def check_in_accounts(account_id):
	return check_exist("select * from accounts where id=\'"+account_id+"\'")

def check_in_accounts_by_name(account_name):
	return check_exist("select * from accounts where name=\'"+account_name+"\'")

def add_account(name):
	if not check_in_accounts_by_name(name):
		insert_db("insert into accounts (name) values (\'"+name+"\')")
		print('添加账户【%s】成功！' %name)
	else:
		print('账户已存在')

def switch_account(_id):
	if check_in_accounts(_id):
		return _id
	else:
		print('当前账户不存在，请重新选择!')

def query_account(_id):
	matches = query_matches('select name from accounts where id=\''+str(_id)+'\'')
	return matches[0]

def check_in_cats(cat_id):
	return check_exist("select * from cats where id=\'"+cat_id+"\'")

def check_in_cats_by_name(cat_name):
	return check_exist("select * from cats where name=\'"+cat_name+"\'")

def query_cats():
	return query_matches("select * from cats")

def show_cats():
	output = '--分类：'
	for cat in query_cats():
		output += str(cat[0]) + '-' + cat[1] + '  '
	print(output+'\n')

def add_cat(name):
	if not check_in_cats_by_name(name):
		insert_db("insert into cats (name) values (\'"+name+"\')")
		print('添加分类【%s】成功！' %name)
	else:
		print('该分类已存在')

def add_record(money, cat, note, account):
	timestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
	sql = "insert into records (money, cat, note, time, account) \
		   				values (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\')"% \
		   					   (money, cat, note, timestr, account)
	if insert_db(sql):
		print('成功记录一笔！')
	else:
		print('添加失败!')

def query_month_total(month, account_id):
	sql = 'SELECT records.money, cats.name'
	sql += ' FROM records LEFT JOIN cats ON records.cat = cats.id'
	sql += ' WHERE records.time LIKE \'____-' + str(month) +'-%\''
	sql += ' AND records.account = \''+str(account_id)+'\''
	return query_matches(sql)

def get_before_month(month):
	if month==1:
		return 12
	else:
		return month-1

def show_months_total(account_id):
	now = datetime.now()
	tmp_month = now.month
	total = 0
	
	while True:
		cost_money = 0
		income_money = 0

		cats_dict = {}
		cats = query_cats()
		for cat in cats:
			cats_dict[cat[1]] = 0

		items = query_month_total(tmp_month, account_id)		
		if len(items) != 0:
			for item in items:
				if str(item[0]).startswith('-'):
					cost_money += item[0]
				else:
					income_money += item[0]
				
				# 计算每月各分类统计
				cats_dict[item[1]] += item[0]

			total += income_money+cost_money

			output = '\n%s月 收入：%s, 支出：%s, 结余：%s \n' %(tmp_month, income_money, cost_money, income_money+cost_money)
			
			for cat in cats:
				cat_name = cat[1]
				cat_total = cats_dict[cat_name]

				if cat_total != 0:
					iscost = str(cat_total).startswith('-')
					# 支出花费
					if iscost and cost_money != 0:
						rate = 100*cat_total/cost_money
						output += '    【%s】共 %s ======== %.1f%%\n' % (cat_name, cat_total, rate)
					elif not iscost and income_money != 0:
						output += '    【%s】共 %s \n' % (cat_name, cat_total)							

			print(output)

		else:
			break
		tmp_month = get_before_month(tmp_month)

	print('总计：%s\n\n' % total)


def is_num(string):
	str1 = str(string)
	if str1.count('.')>1:#判断小数点是不是大于1
		return False
	elif str1.count('-')>1:
		return False
	else:
		strs  = str1.split('.')#按小数点分割字符
		frist_num = strs[0] #取分割完之后这个list的第一个元素
		frist_num = frist_num.replace('-','')#把负号替换成空

		if len(strs)==1 and frist_num.isdigit():
			return True
		elif len(strs)==2 and frist_num.isdigit() and strs[1].isdigit():
		#如果小数点两边都是整数的话，那么就是一个小数
			return True
		else:
			return False


def main(argv=None):

	setup_db()
	show_cats()
	
	cur_account = '1'

	while True:
		print('当前为%s.' %(query_account(cur_account)))

		input_str = input('记一笔：')

		if input_str.startswith('show'):
			strs = input_str.split(' ')
			if len(strs)==1:
				show_months_total('1')
			elif strs[1].isdigit():
				show_months_total(strs[1])
			else:
				print('格式输入错误..')
			continue
		elif input_str == 'q':
			return 0
		elif input_str.startswith('cat'):
			strs = input_str.split(' ')
			if len(strs)==1:
				show_cats()
			else:
				add_cat(strs[1])
			continue
		elif input_str.startswith('account'):
			strs = input_str.split(' ')
			if len(strs) == 1:
				show_accounts()
			elif strs[1].isdigit():
				cur_account = switch_account(strs[1])
			else:
				add_account(strs[1])
			continue


		strs = input_str.split(' ')

		if len(strs) < 2:
			print('格式输入错误..')
			continue

		money = strs[0]
		cat = strs[1]
		note = ''
		if len(strs)==3:
			note = strs[2]

		if not is_num(money):
			print('金额输入错误..')
		elif not cat.isdigit():
			print('分类输入错误..')
		elif not check_in_cats(cat):
			print('没有该分类!')
		else: # 记录到数据文件
			add_record(money, cat, note, cur_account)


if __name__ == "__main__":
	sys.exit(main())


