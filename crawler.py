#!/usr/bin/env python


import getopt
import sys
import httplib
import urllib2
import re
import HTMLParser
import urlparse


PROG='crawler'
VERSION='1.0'
USERAGENT='Crawler/' + VERSION

HTTPRE = re.compile('^http')


class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):
	def http_error_default(self, req, fp, code, msg, headers):
		result = urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)
		result.status = code
		return result


class LinkHtmlParser(HTMLParser.HTMLParser):
	def __init__(self, url, local=False, domain=False):
		HTMLParser.HTMLParser.__init__(self)
		self.url = url
		self.local = local
		self.domain = domain
		self.links = []

	def set_url(self, url):
		self.url = url

	def set_local(self, local):
		self.local = local

	def set_domain(self, domain):
		self.domain = domain

	def reset_links(self):
		self.links = []

	def handle_starttag(self, tag, attrs):
		if tag != 'a':
			return

		website = urlparse.urlparse(self.url).netloc

		for name, value in attrs:
			if name == 'href' and len(value):
				if not HTTPRE.match(value):
					value = urlparse.urljoin(self.url, '/'+value if value[0]=='#' else value)
				if value not in self.links:
					location = urlparse.urlparse(value).netloc
					if self.local and website != location:
						continue
					if self.domain:
						value = location
					self.links.append(value)


class Crawler:
	def __init__(self, url, useragent=USERAGENT):
		self.url = url
		self.request = urllib2.Request(url)
		self.request.add_header('User-Agent', useragent)
		opener = urllib2.build_opener(DefaultErrorHandler())
		try:
			self.data = opener.open(self.request)
		except urllib2.URLError as err:
			print str(err)
			self.data = None

	def get_code(self):
		return self.data.code if self.data else 404

	def get_data(self):
		return self.data.read().decode("utf-8", errors='ignore')


def usage():
	print "usage: %s [options] <url>" % (PROG)
	print "options:"
	print "\t-h | --help             : display this and exit."
	print "\t-v | --version          : display version and exit."
	print "\t-d | --debug            : set the debug on."
	print "\t-u | --user-agent  <ua> : set the user agent."
	print "\t-r | --recursive        : recursive mode."
	print "\t-l | --local            : stay in the web site."
	print "\t-D | --domain           : search for domain only."


def version():
	print "%s %s" % (PROG, VERSION)


def extend_links(links, url, local, domain):
	parser = LinkHtmlParser(url, local, domain)
	crawler = Crawler(url)

	if crawler.get_code() == 200:
		parser.feed( crawler.get_data() )
		links.extend(x for x in parser.links if x not in links)

	return links


if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:],
				"hvdu:rlD",
				["help", "version", "debug", "user-agent=", "recursive", "local", "domain"])
	except getopt.GetoptError as err:
		print str(err)
		sys.exit(-1)

	recursive = False
	local = False
	domain = False

	for o,a in opts:
		if o in ('-h', '--help'):
			usage()
			sys.exit()
		elif o in ('-v', '--version'):
			version()
			sys.exit()
		elif o in ('-d', '--debug'):
			httplib.HTTPConnection.debuglevel = 1
		elif o in ('-u', '--user-agent'):
			USERAGENT = a
		elif o in ('-r', '--recursive'):
			recursive = True
		elif o in ('-l', '--local'):
			local = True
		elif o in ('-D', '--domain'):
			domain = True
		else:
			assert False, "Unhandled option"

	if not len(args):
		print "No URL found"
		sys.exit(-1)

	links = []

	for url in args:
		links = extend_links(links, url, local, domain)

	if recursive:
		for link in links:
			print link
			if HTTPRE.match(link):
				links = extend_links(links, link, local, domain)
	else:
		for link in links:
			print link
