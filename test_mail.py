#!/usr/bin/env python3

import argparse
from configparser import RawConfigParser
import os
import io

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


import psycopg2
import psycopg2.extras

def load_config(config_file_path):
	ini_str = '[root]\n' + open(config_file_path, 'r').read()
	ini_fp  = io.StringIO(ini_str)
	config = RawConfigParser(strict=False, allow_no_value=True)
	config.readfp(ini_fp)
	return config


def parse_args():
	parser = argparse.ArgumentParser(description="Email ")
	parser.add_argument('-c', '--config', required=True,
						dest="config", help="Config File")
	parser.add_argument('-r', '--receiver', required=True,
			            dest="receiver", help="Receiver Mail Address")

	args = parser.parse_args()
	return args


def get_smtp_info(config):
	sql = """SELECT smtphost as host,smtpport as port,emailusername as username,emailpassword as password,loginemail as is_auth,
				fromemail as from_email, smtp_secure as smtp_secure FROM system_parameter LIMIT 1"""

	conn = psycopg2.connect(host=config.get('root', 'db_host'), 
							port=config.get('root', 'db_port'), 
							database=config.get('root', 'db_name'),
							user=config.get('root', 'db_username'), 
							password=config.get('root', 'db_password'))
	conn.autocommit = True
	cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	cursor.execute(sql)
	smtp_setting = cursor.fetchone()
	cursor.close()
	conn.close()
	return smtp_setting	

def send_mail(email_address, smtp_setting):
	smtp_info = smtp_setting

	msg = MIMEMultipart()	
	msg['Subject'] = 'For testing'
	msg['From'] = smtp_info['from_email']
	msg['to'] = email_address
	msg['Content'] = 'For testing'
	if smtp_info['smtp_secure'] == 2:
		smtp = smtplib.SMTP_SSL(smtp_info['host'], smtp_info['port'])
	else:
		smtp = smtplib.SMTP(smtp_info['host'], smtp_info['port'])

	try:
		smtp.set_debuglevel(True)
		smtp.ehlo()
		if smtp_info['smtp_secure'] == 1:
			smtp.starttls()
			smtp.ehlo()
		smtp.login(smtp_info['username'], smtp_info['password'])
		smtp.sendmail(smtp_info['from_email'], email_address, msg.as_string())
	except smtplib.SMTPException as e:
		mail_response = e.smtp_error.decode()
	else:
		mail_response = 'OK'
	finally:
		smtp.quit()



def main():
	args = parse_args()
	config =load_config(args.config)
	smtp_setting = get_smtp_info(config)
	send_mail(args.receiver, smtp_setting)

if __name__ == "__main__":
	main()
