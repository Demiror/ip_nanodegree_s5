import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(template_dir),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

DEFAULT_NOTEBOOK_NAME = 'Stage 5'

def notebook_key(notebook_name=DEFAULT_NOTEBOOK_NAME):
	"""Constructs a Datastore key for a Notebook entity.

	We use notebook_name as the key.
	"""
	return ndb.Key('Notebook', notebook_name)

def current_user(self):
	user = users.get_current_user()
	if user:
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
	return user, url, url_linktext

class Author(ndb.Model):
	"""Sub model for representing an author."""
	identity = ndb.StringProperty(indexed=False)
	email = ndb.StringProperty(indexed=False)


class Comment(ndb.Model):
	author = ndb.StructuredProperty(Author)
	comment_content = ndb.StringProperty(indexed=False)
	date = ndb.DateTimeProperty(auto_now_add=True)

class Note(ndb.Model):
	"""A main model for representing an individual Notebook entry."""
	author = ndb.StructuredProperty(Author)
	title = ndb.StringProperty(indexed=False)
	content = ndb.StringProperty(indexed=False)
	comments = ndb.StructuredProperty(Comment, repeated=True)
	date = ndb.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = JINJA_ENVIRONMENT.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class MainPage(Handler):
	def get(self):
		notebook_name = self.request.get('notebook_name',
										  DEFAULT_NOTEBOOK_NAME)
		notes_query = Note.query(
			ancestor=notebook_key(notebook_name)).order(Note.date)
		num_notes = 10
		notes = notes_query.fetch(num_notes)

		user, url, url_linktext = current_user(self)

		comment_error = self.request.get('comment_error')

		self.render('index.html', 
			user=user, 
			notes=notes,
			notebook_name=notebook_name, 
			url_notebook_name=urllib.quote_plus(notebook_name), 
			url=url, 
			url_linktext=url_linktext,
			comment_error=comment_error)

	def post(self):
		note_id = self.request.get('key')
		note_key = ndb.Key(urlsafe=note_id)
		note = note_key.get()        

		comment = Comment(parent=note_key)

		if users.get_current_user():
			comment.author = Author(
					identity=users.get_current_user().user_id(),
					email=users.get_current_user().email())

		comment_error = False
		comment_content = self.request.get('comment_content').strip()
		if comment_content:
			comment.comment_content = comment_content
			comment.put()
			note.comments.append(comment)
			note.put()
			self.redirect('/#%s' % note_id)
		else:
			comment_error = note_id
			self.redirect('/?comment_error=%s#%s' % (comment_error, note_id))


class Add_Note_Page(Handler):
	def get(self):
		notebook_name = self.request.get('notebook_name',
										  DEFAULT_NOTEBOOK_NAME)
		
		user, url, url_linktext = current_user(self)

		note_error = self.request.get('note_error')

		self.render('add_note.html', 
			notebook_name=notebook_name,
			url_notebook_name=urllib.quote_plus(notebook_name),
			url=url, 
			url_linktext=url_linktext,
			note_error=note_error)

class Submit_Note(Handler):
	def post(self):
		notebook_name = self.request.get('notebook_name',
										  DEFAULT_NOTEBOOK_NAME)
		note = Note(parent=notebook_key(notebook_name))

		if users.get_current_user():
			note.author = Author(
					identity=users.get_current_user().user_id(),
					email=users.get_current_user().email())

		note.title = self.request.get('title').strip()
		note.content = self.request.get('content').strip()

		note_error = False

		if note.title and note.content:
			note.put()
			self.redirect('/?' + urllib.quote_plus(notebook_name))
		else:
			note_error = True
			self.redirect('/add_note?note_error=%s' % note_error)

app = webapp2.WSGIApplication([
	('/', MainPage),
	('/add_note', Add_Note_Page),
	('/submit_note', Submit_Note),
], debug=True)