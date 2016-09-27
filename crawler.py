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
	def set_url(self, url):
		self.url = url

	def reset_links(self):
		self.links = []

	def handle_starttag(self, tag, attrs):
		if tag != 'a':
			return

		for name, value in attrs:
			if name == 'href' and len(value):
				if not HTTPRE.match(value):
					value = urlparse.urljoin(self.url, '/'+value if value[0]=='#' else value)
				if value not in self.links:
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


def version():
	print "%s %s" % (PROG, VERSION)


def extend_links(links, url):
	parser = LinkHtmlParser()
	crawler = Crawler(url)

	if crawler.get_code() == 200:
		parser.set_url(url)
		parser.reset_links()
		parser.feed( crawler.get_data() )
		links.extend(x for x in parser.links if x not in links)

	return links


if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hvdu:r", ["help", "version", "debug", "user-agent=", "recursive"])
	except getopt.GetoptError as err:
		print str(err)
		sys.exit(-1)

	recursive = False

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
		else:
			assert False, "Unhandled option"

	if not len(args):
		print "No URL found"
		sys.exit(-1)

	links = []

	for url in args:
		extend_links(links, url)

	if recursive:
		for link in links:
			print link
			if HTTPRE.match(link):
				links = extend_links(links, link)
	else:
		for link in links:
			print link
