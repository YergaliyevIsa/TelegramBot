import telebot
import requests
from datetime import date, timedelta
import datetime as DT
import os.path
import matplotlib.pyplot as plt

def get_exchange_from_site(url = 'https://api.exchangeratesapi.io/latest?base=USD'):
	resp = requests.get(url)
	data = eval(resp.text)['rates']
	ans = ''
	for corrency in data:
		ans += f'{corrency} {round(data[corrency], 2)}\n'
	return ans

def get_exchange_from_local(path):
	print('local')
	ans = ''
	with open(path, 'r') as f:
		ans = f.read()
	return ans

def save_to_local(data, path):
	with open(path, 'w') as f:
		f.write(data)


def save_req_time(last_time, path):
	with open(path, 'w') as f:
		f.write(str(last_time))

def get_prev_time(path):
	with open(path, 'r') as f:
		prev_time = f.read()
	prev_ymd, prev_hms = prev_time.split()
	year, month, day = list(map(int, prev_ymd.split('-')))
	hour, minute, second = list(map(int, prev_hms[:8].split(':')))
	return DT.datetime(year, month, day, hour, minute, second)
 
def make_plot(data, dest_con):
	x = [(key, data[key][dest_con]) for key in data]
	x.sort(key = lambda a : a[0])
	y = [i[1] for i in x]
	plt.plot([i[0] for i in x], y, label = 'exchange_rate')
	plt.xlabel('date')
	plt.ylabel('rate')
	plt.legend()
	plt.savefig('rate.png')


TOKEN = 'here must be api_key of telegram bot'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text'])
def send_answer(message):
	local_database = 'exchange_rate.txt'
	last_req = 'last_time.txt'
	if message.text == '/list' or message.text == '/lst':
		if os.path.exists(last_req):
			cur_time = DT.datetime.now()
			if cur_time - get_prev_time(last_req) < timedelta(minutes = 10):
			#	print('here')
				ans = get_exchange_from_local(local_database)
			else:
				ans = get_exchange_from_site()
				save_to_local(ans, local_database)
			save_req_time(cur_time, last_req)
		else:
			save_req_time(DT.datetime.now(), last_req)
			ans = get_exchange_from_site()
			save_to_local(ans, local_database)
		bot.send_message(message.from_user.id, ans)

	elif message.text[:9]  == '/exchange':
		currency_list = ['CAD', 'HKD', 'ISK', 'PHP', 'DKK', 'HUF', 'CZK', 'GBP', 'RON', 'SEK', 'IDR', 
						 'INR', 'BRL', 'RUB', 'HRK', 'JPY', 'THB', 'CHF', 'EUR', 'MYR', 'BGN', 'TRY', 
						 'CNY', 'NOK', 'NZD', 'ZAR', 'USD', 'MXN', 'SGD', 'AUD', 'ILS', 'KRW', 'PLN']
		req = message.text.split()
		resp = requests.get('https://api.exchangeratesapi.io/latest?base=USD')
		data = eval(resp.text)['rates']
		if len(req) == 5:
			if req[1].isdigit() and req[2] in currency_list and req[4] in currency_list:
								
				ans = data[req[4]] / data[req[2]] * float(req[1])
				bot.send_message(message.from_user.id, round(ans, 2))
			else:
				bot.send_message(message.from_user.id, 'Convertation impossible')
		else:
			bot.send_message(message.from_user.id, 'Convertation impossible')		

	elif message.text[:8] == '/history':
		source_con, dest_con = message.text[9:].split('/')
		today, seven_days_bef = date.today(), date.today() - timedelta(days = 7)
		url = f'https://api.exchangeratesapi.io/history?start_at={str(seven_days_bef)}&end_at={str(today)}'
		param = '&base=' + source_con + '&symbols=' + dest_con 
		try:
			resp = requests.get(url + param)
		except Exception as e:
			bot.send_message(message.from_user.id, 'Try again')
		else:
			resp = requests.get(url + param)
			data = eval(resp.text)['rates']
			make_plot(data, dest_con)
			bot.send_photo(message.from_user.id, photo = open('rate.png', 'rb'))		
	else:
		bot.send_message(message.from_user.id, 'bot do not understand command')
		#bot.send_message(message.from_user.id, "Рамазан гей")

bot.polling()

