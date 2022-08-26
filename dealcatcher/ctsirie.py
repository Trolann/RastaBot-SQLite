from dealcatcher.utils import get_site
from rastadb import dealcatcher_db
from time import sleep

CTS_WEBSITE = 'https://chitownseeds.com/vendor/irie-genetics/'
page_str = '?product-page={}'
item_start_str = "product type-product" # Generates an item's start_index in Deal object
thumbnail = "https://chitownseeds.com/wp-content/uploads/2021/01/ChitownSeeds-logo_small.png"
acronym = 'cts'
expired_table = 'deals_expired'
new_table = 'deals_new'


class CTSDeal:
	def __init__(self, website_html, start_index):
		self.name = self.get_name(website_html, start_index)
		self.url = self.get_url(website_html, start_index)
		self.image_url = self.get_image_url(website_html, start_index)
		self.amount = self.get_amount(website_html, start_index)
		self.in_stock = self.check_stock()
		self.description = ''
		self.reference_id = { # deal.reference_id.get(key)
			'discord': -1,
			'sheets' : -1
		}

	def __lt__(self, other):
		if type(other) is type(self):
				return (self.name < other.name)
		else:
			return NotImplemented

	def __le__(self, other):
			return (self.name <= other.name)

	def __gt__(self, other):
		return (self.name > other.name)

	def __ge__(self, other):
			return (self.name >= other.name)

	def __eq__(self, other):
		if type(other) is type(self):
			return (self.name == other.name)
		else:
			return NotImplemented

	def __ne__(self, other):
		if type(other) is type(self):
			return (self.name != other.name)
		else:
			return NotImplemented

	def __hash__(self):
		return hash(str(self))

	def get_name(self, website_html, start_index):
		item = "woocommerce-loop-product__title\">"
		terminal = "</h2>"
		name = website_html[ website_html.find(item, start_index) + len(item) : website_html.find(terminal, website_html.find(item, start_index) + len(item)) ]	
		return name

	def get_url(self, website_html, start_index):
		item = "a href=\""
		terminal = "\" class="
		url = website_html[ website_html.find(item, start_index) + len(item) : website_html.find(terminal, website_html.find(item, start_index) + len(item)) ]	
		return url

	def get_amount(self, website_html, start_index):
		# For now, if there's a sale just run the price search again and get the sale amount.
		# Pull out normal price
		item = '&#36;</span>'
		terminal = "</bdi>"
		amount = website_html[website_html.find(item, start_index) + len(item) : website_html.find(terminal, website_html.find(item, start_index) + len(item)) ]
		
		# If there's a sale, pull out sale amount
		if website_html.find("Sale!", start_index) > 0:
			start_index = website_html.find(item, start_index) + 1 # Start at the normal price
			amount = website_html[website_html.find(item, start_index) + len(item) : website_html.find(terminal, website_html.find(item, start_index) + len(item)) ]
		return float(amount)

	def get_image_url(self, website_html, start_index):
		item = "src=\""
		terminal = "\" class="
		url = website_html[ website_html.find(item, start_index) + len(item) : website_html.find(terminal, website_html.find(item, start_index) + len(item)) ]	
		return url

	def check_stock(self):
		product_html = get_site(self.url)
		if "out-of-stock" in product_html:
			return False
		return True	

def get_pages(html):
	pages = 1
	page_index = 0
	
	while html.find(page_str.format(pages + 1), page_index) != -1:
		pages += 1
		page_index = html.find(page_str.format(pages), page_index + 1)

	return int(pages)

def get_all_cts_deals(website):
	current_deals = []
	# Get a copy of the source
	html = get_site(website)

	num_pages = get_pages(html)
	for page in range(1, num_pages + 1):

		if page != 1:
			html = get_site('{}{}'.format(website, page_str.format(page)))

		start_index = html.find(item_start_str)
		while(start_index != -1):
			deal_to_add = CTSDeal(html, start_index)

			if deal_to_add.in_stock:
				current_deals.append(deal_to_add)
				start_index = html.find(item_start_str, start_index + 1)
			else:
				start_index = html.find(item_start_str, start_index + 1)

	return current_deals

def process_cts_deals(old_cts_deals): # Take old list, get new list, produce print/expired/update the old list
	deals_to_print = []
	expired_deals = []

	active_cts_deals = get_all_cts_deals(CTS_WEBSITE)

	for new_deal in active_cts_deals:
		if new_deal not in old_cts_deals:
			deals_to_print.append(new_deal)

	for old_deal in old_cts_deals:
		if old_deal not in active_cts_deals:
			expired_deals.append(old_deal)

	old_cts_deals = active_cts_deals.copy()

	return (old_cts_deals, deals_to_print, expired_deals)

def cts_daemon(sleep_time):
	print('ChiTownSeeds Daemon started')
	
	old_deals = []
	first_run = True

	run = 0
	while True:
		run += 1

		old_deals, new_deals, expired_deals = process_cts_deals(old_deals)

		new_deals_list = list()
		for deal in new_deals:
			new_deals_list.append((deal.name, deal.url, deal.image_url, deal.amount, deal.in_stock, deal.description))

		expired_deals_list = list()
		for deal in expired_deals:
			expired_deals_list.append(
				(deal.name, deal.url, deal.image_url, deal.amount, deal.in_stock, deal.description))

		for deal in new_deals_list:
			dealcatcher_db.new_deal(acronym, deal, first_run=first_run)
		for deal in expired_deals_list:
			dealcatcher_db.expired_deal(acronym, deal)
		sleep(sleep_time)
