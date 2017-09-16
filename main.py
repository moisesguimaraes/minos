#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import jinja2
import webapp2

from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

data_dir = os.path.join(os.path.dirname(__file__), "data")

gestao_comercial_data = json.loads(open(os.path.join(data_dir, "gestao_comercial.json")).read())

gestao_comercial_html = jinja_env.get_template("gestao_comercial.html").render(curso=gestao_comercial_data)



class Admin(ndb.model):
    usuario = ndb.StringProperty(indexed=False)
    senha = ndb.StringProperty(indexed=False)
    cookie = ndb.StringProperty(indexed=False)


class Aluno(ndb.model):
    matricula = ndb.StringProperty(indexed=False)
    materias = ndb.JsonProperty()
    finalizado = ndb.BooleanProperty()
    codigo = ndb.StringProperty(indexed=False)


class Handler(webapp2.RequestHandler):
    
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **kw):
        template = jinja_env.get_template(template)
        return template.render(kw)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainHandler(Handler):

    def get(self):
        self.write(gestao_comercial_html)


class Login(Handler):

    def get(self):
        self.write("login.html")

    def post(self):
        usuario = self.request.get('usuario')
        senha = self.request.get('senha')
        admin = Admin(parent= ndb.Key('admin','admin'))
        if usuario == admin.usuario and senha == admin.senha :
            admin.cookie = ""
            self.response.headers['cookie'] = ""
            self.redirect('/admin')
        else:
            self.redirect('/login')

    def delete(self):
        cookie = self.request.headers.get("cookie")
        admin = Admin(parent= ndb.Key('admin','admin'))
        if cookie == True:
            admin.cookie = ""
            self.response.headers['cookie'] = ""
            self.redirect('/login')
        else:
            self.redirect('/login')


class Administrador(Handler):

    def get(self):
        cookie = self.request.headers.get("cookie")
        admin = Admin(parent= ndb.Key('admin','admin'))
        if cookie == admin.cookie:
            self.render("administrador.html", "")
        else:
            self.redirect("/login")

    def post(self):
        cookie = self.request.headers.get("cookie")
        admin = Admin(parent= ndb.Key('admin','admin'))
        if cookie == admin.cookie:
            # tratar formulario submetido
        else:
            self.redirect('/login')


class Formulario(Handler):

    def get(self):
        matricula = self.request.get('matricula', '')
        aluno = Aluno(parent=ndb.Key('matricula',''))
        if matricula != '' and matricula == aluno.matricula :
            if aluno.finalizado == True:
                self.redirect('/#')
            else:
                """
                então montar o questinario e devolver 
                """
        else:
            self.redirect('/#')
    
    def post(self):
        matricula = self.request.get('matricula', '')
        disciplinas = self.request.get_all('d')
        codigo = self.request.get('c')
        aluno = Aluno(parent=ndb.Key('matricula',''))
        #processar as disciplinas respondidas
        aluno.finalizado = True
        aluno.codigo = codigo
        self.redirect('/#')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin', Administrador),
    ('/login', Login),
    ('/avaliar', Formulario),
], debug=True)
