from selenium import webdriver
from time import sleep

# read cookies from file
# format
# ... expiry1 key1 value1
# ... expiry2 key2 value2
def read_cookies(p = 'cookies.txt'):
    cookies = []
    with open(p, 'r') as f:
        for e in f:
            e = e.strip()
            if e.startswith('#'): continue
            k = e.split('\t')
            if len(k) < 3: continue	# not enough data
            # with expiry
            cookies.append({'name': k[-2], 'value': k[-1], 'expiry': int(k[-3])})
    return cookies

print(read_cookies())

def run():
	cookies = read_cookies()
	print ('[+] Read {} cookies'.format(len(cookies)))
	print (cookies)
	d = webdriver.Chrome()
	# adding cookies
	for c in cookies: d.add_cookie(c)
	print ('')
	print ('[+] Added cookies')
	print(d.get_cookies())

	d.get('https://instagram.com')
	sleep(2)
	print(d.get_cookies())
	sleep(50)
def main():
	print ('[+] Selenium cookies importer')
	try: run()
	except Exception as ex: print ('[!] Error: {}'.format(ex))
	finally: print ('[+] Finished !')
main()