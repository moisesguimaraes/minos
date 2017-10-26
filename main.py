#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import jinja2
import webapp2

from hashlib import sha224
from datetime import datetime
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

data_dir = os.path.join(os.path.dirname(__file__), "data")

gestao_comercial_data = json.loads(open(os.path.join(data_dir, "gestao_comercial.json")).read())

gestao_comercial_html = jinja_env.get_template("gestao_comercial.html").render(curso=gestao_comercial_data)

data_cookies = dict()


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


class Aluno(Handler):

    def get(self):
        self.render("loginAluno.html")

    def post(self):
        matricula = self.request.get('mat')
        # aluno = ndb.Key("mat", matricula).get()
        aluno = {"matricula": 123}
        if matricula == aluno['matricula']:
            url1 = {"mat": matricula}
            self.redirect('/formularios?' + urllib.urlencode(url1))
        else:
            self.redirect('/aluno')


class Formularios(Handler):

    def get(self):
        matricula = self.request.get('mat')
        # aluno = ndb.Key("mat", matricula).get()
        aluno = {"matricula": 123, "formularios" : 1 }
        if matricula == aluno.matricula:
            self.render("formularios.html", disciplinas)
        else:
            self.redirect('/aluno')


class Avaliacao(Handler):
    def get(self):
        quest = {
            "formulario": {
                "titulo": "formulario 1",
                "url": "/avaliar?123",
                "questao": {
                    "numero": 1,
                    "enunciado": "com quantos paus se faz uma canoa?",
                    "materias": {
                        "materia1": {"nome": "Portugues", "respostas": [1, 2, 3]},
                        "materia2": {"nome": "Matematica", "respostas": [1, 2, 3]},
                        "materia3": {"nome": "Biologia", "respostas": [1, 2, 3]},
                        "materia4": {"nome": "Filosofia", "respostas": [1, 2, 3]},
                        "materia5": {"nome": "Quimica", "respostas": [1, 2, 3]}},
                    "tipo": "texto"
                 }
            }
        }
        t = jinja_env.get_template("formulario3.html")
        self.response.out.write(t.render(quest))
    """def get(self):
        form = self.request.get("form")
        mat = self.request.get("mat")
        aluno = ndb.Key('mat', mat).get()
        if mat == aluno.matricula:
            progresso = aluno.progresso[form]
            disciplinas = aluno.disciplinas
            formulario = disciplinas[0].formulario"""

class Login(Handler):

    def get(self):
        self.write("login.html")

    def post(self):
        usuario = self.request.get('usuario')
        senha = self.request.get('senha')
        admin = Admin(parent=ndb.Key('admin','admin'))
        if usuario == admin.usuario and senha == admin.senha :
            dtime = datetime.now()
            temp_cookie = sha224(dtime.isoformat()).hexdigest()
            data_cookies[temp_cookie] = admin
            self.response.headers.add_header("Cookie", temp_cookie)
            self.redirect('/admin')
        else:
            self.redirect('/login')

    def delete(self):
        cookie = self.request.headers.get("Cookie")
        if cookie in data_cookies.keys():
            data_cookies.pop(cookie)
            self.response.headers.add_header("Cookie", None)
            self.redirect('/login')
        else:
            self.redirect('/login')


class Administrador(Handler):

    def get(self):
        cookie = self.request.headers.get("cookie")
        admin = Admin(parent= ndb.Key('admin','admin'))
        if cookie in data_cookies.keys():
            self.render(template_dir + "/administrador.html", "")
        else:
            self.redirect("/login")

    def post(self):
        cookie = self.request.headers.get("cookie")
        admin = Admin(parent= ndb.Key('admin','admin'))
        if cookie in data_cookies.keys():
            # tratar formulario submetido
            pass
        else:
            self.redirect('/login')


class Formularios(Handler):

    def get(self):
        matricula = self.request.get('matricula')
        aluno = Aluno(parent=ndb.Key('matricula'))
        if matricula != '' and matricula == aluno.matricula :
            if aluno.finalizado == True:
                self.redirect('/#two')
            else:
                pass
                """
                então montar o questinario e devolver 
                """
        else:
            self.redirect('/#two')
    
    def post(self):
        matricula = self.request.get('matricula', '')
        disciplinas = self.request.get_all('d')
        codigo = self.request.get('c')
        aluno = Aluno(parent=ndb.Key(matricula,''))
        #processar as disciplinas respondidas
        aluno.finalizado = True
        aluno.codigo = codigo
        self.redirect('/#')


class Codigo(Handler):

    def get(self):
        self.write(template_dir + "codigo.html")

    def post(self):
        codigo = self.request.get('c')
        matricula = self.request.get('matricula')
        aluno = Aluno(parent=ndb.key(matricula, ''))
        if matricula == aluno.matricula and codigo == aluno.codigo and aluno.codigo_usado != True:
            aluno.codigo_usado = True
            #responder com codigo valido
        else:
            pass
            #responder com codigo não valido


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/aluno', Aluno),
    ('/formularios', Formularios),
    ('/avaliar', Avaliacao),
    ('/admin', Administrador),
    ('/login', Login),
    ('/professor', Codigo)
], debug=True)
