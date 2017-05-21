#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import jinja2
import webapp2

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

data_dir = os.path.join(os.path.dirname(__file__), "data")
gestao_comercial_data = json.loads(
    open(os.path.join(data_dir, "gestao-comercial.json")).read())

gestao_comercial_html = jinja_env.get_template("index.html").render(
    curso=gestao_comercial_data)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **kw):
        t = jinja_env.get_template(template)
        return t.render(kw)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainHandler(Handler):
    def get(self):
        self.write(gestao_comercial_html)

class DisciplinasHandler(Handler):
    def post(self):
        self.response.write(self.request.get_all('d'))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/disciplinas', DisciplinasHandler)
], debug=True)
