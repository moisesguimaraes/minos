#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import jinja2
import webapp2

from google.appengine.ext import ndb

from models import Disciplina

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainHandler(Handler):
    def get(self):
        self.render("index.html")

class DisciplinasHandler(Handler):
    def post(self):
        self.response.write(self.request.get_all('disciplina'))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/disciplinas', DisciplinasHandler)
], debug=True)
