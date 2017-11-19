#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import jinja2
import time
import webapp2
import urllib

from datetime import datetime
from hashlib import sha224
from os.path import dirname, join
from google.appengine.ext import ndb
from models import *

TEMPLATE_DIR = join(dirname(__file__), "templates")
DATA_DIR = join(dirname(__file__), "data")
GESTAO_COMERCIAL_DATA = json.loads(open(join(
    DATA_DIR, "gestao_comercial.json")).read())

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR), autoescape=True)
GESTAO_COMERCIAL_HTML = JINJA_ENV.get_template(
    "gestao_comercial.html").render(curso=GESTAO_COMERCIAL_DATA)


DATA_COOKIE = dict()


def gerador_cookie():
    dtime = datetime.now()
    return str(sha224(dtime.isoformat()).hexdigest())


class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, *template, **kw):
        t = JINJA_ENV.get_template(*template)
        return t.render(**kw)

    def render(self, *template, **kw):
        self.write(self.render_str(*template, **kw))

class MainHandler(Handler):

    def get(self):
        self.write(GESTAO_COMERCIAL_HTML)


class AlunoHandler(Handler):

    def get(self):
        self.render("loginAluno.html")

    def post(self):
        global DATA_COOKIE
        try:
            matricula = int(self.request.get('mat'))
            aluno = ndb.Key(Aluno, matricula).get()
            if (aluno != None) and (matricula == int(aluno.matricula)):
                cookie = gerador_cookie()
                data = {
                    'perm': 2,
                    'mat': matricula,
                    'form': None
                }
                DATA_COOKIE[cookie] = data
                self.response.set_cookie(key='__ck',value=cookie)
                self.redirect('/formularios')
            else:
                self.redirect('/aluno')
        except ValueError:
            self.redirect('/aluno')


class LoginHandler(Handler):

    def get(self):
        self.render("loginAdmin.html")

    def post(self):
        global DATA_COOKIE
        try:
            usuario = self.request.get('usuario')
            senha = self.request.get('senha')
            if usuario == "a" and senha == "a":
                cookie = gerador_cookie()
                data = {
                    "perm": 2,
                    "aluno": None,
                    "materia": None,
                    "formulario": None,
                    "pergunta": None
                }
                DATA_COOKIE[cookie] = data
                self.response.set_cookie(key='__ck', value=cookie)
                self.redirect('/admin')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')


class FormulariosHandler(Handler):

    def get(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data and data['perm'] == 2:
                forms = Formulario.query(Formulario.alunos.IN([str(data['mat'])]))
                form = []
                for formu in forms:
                    d = {
                        "titulo": formu.titulo,
                        "descricao": formu.descricao,
                        "codigo": formu.user_id,
                        "progresso": 0}
                    form.append(d)
                self.render("formularios.html", formularios=form)
            else:
                self.redirect('/aluno')
        except ValueError:
            self.redirect('/aluno')

    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            form = self.request.get('form')
            if data and data['perm'] == 2 and form != '':
                data['form'] = int(form)
                self.redirect('/avaliar')
            else:
                self.redirect('/aluno')
        except ValueError:
            self.redirect('/aluno')


class AvaliacaoHandler(Handler):
    def get(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data and data['perm'] == 2:
                form = data['form']
                formu = ndb.Key(Formulario, form).get()
                lista_perguntas = list(map(int, formu.perguntas))
                lista_materias = list(map(int, formu.materias))
                materias = Materia.query(Materia.user_id.IN(lista_materias))
                pergunta = ndb.Key(Pergunta, lista_perguntas[0]).get()
                page = {
                    "formulario": formu,
                    "numero": 1,
                    "pergunta": pergunta,
                    "materias": materias
                }
                self.render('questao.html', page=page)
            else:
                self.redirect('/aluno')
        except ValueError:
            self.redirect('/aluno')

    def post(self):
        form = int(self.request.get("form"))
        formu = ndb.Key(Formulario, form).get()
        lista_materias = list(map(int, formu.materias))
        lista_perguntas = list(map(int, formu.perguntas))
        materias = Materia.query(Materia.user_id.IN(lista_materias))
        pergunta = Pergunta.query(Pergunta.user_id.IN(lista_perguntas[pos]))
        resultados = []
        for materia in materias:
            resu = Resultado(aluno=int(aluno.matricula), formulario=form, enunciado=pergunta.enunciado, respostas = str( materia.titulo + " : " + ", ".join(self.request.get_all(materia.titulo))))
            resultados.append(resu)
        ndb.put_multi(resultados)
        time.sleep(.2)


class CodigoHandler(Handler):

    def get(self):
        #alguma forma de identificar
        cont = ndb.Key(Contador, 1).get()
        cod = Codigo(nomeAluno=aluno.nome, periodo=aluno.periodo, codigo=str("GEST" + cont.maior_cod))
        cod.put()
        time.sleep(.1)
        self.write("gratificacao.html", codigo=cod.codigo)


class AdministradorHandler(Handler):

    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            self.render("Administrador.html")
        else:
            self.redirect('/login')


class ListarFormularios(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            formularios = Formulario.query()
            page = {
                "titulo": u"Formulários",
                "formularios": formularios
            }
            self.render("Administrador.html", page=page)
        else:
            self.redirect('/login')


class ListarAlunos(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            alunos = Aluno.query()
            page = {
                "titulo": "Alunos",
                "alunos": alunos
            }
            self.render("Administrador.html", page=page)
        else:
            self.redirect('/login')


class ListarMaterias(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            materias = Materia.query()
            page = {
                "titulo": u"Matérias",
                "materias": materias
            }
            self.render("Administrador.html", page=page)
        else:
            self.redirect('/login')


class ListarPerguntas(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            perguntas = Pergunta.query()
            page = {
                "titulo": "Perguntas",
                "perguntas": perguntas
            }
            self.render("Administrador.html", page=page)
        else:
            self.redirect('/login')


class CriarFormulario(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            perguntas = Pergunta.query()
            page = {
                "tipo": 1,
                "perguntas": perguntas
            }
            self.render("criarformulario.html", page=page)
        else:
            self.redirect('/login')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            titulo = self.request.get('titulo')
            descricao = self.request.get('descricao')
            perguntas = self.request.get_all('perg')
            if perguntas:
                perguntas = list(map(int, perguntas))
            cont = ndb.Key(Contador, 1).get()
            if not cont:
                cont = Contador(id_formularios=1, id_perguntas=1, id_materias=1, id=1)
            form = Formulario(titulo=titulo, descricao=descricao, perguntas=perguntas, id=cont.id_formularios, user_id=cont.id_formularios)
            cont.id_formularios += 1
            cont.put()
            form.put()
            time.sleep(.1)
            self.redirect('/listarformularios')
        else:
            self.redirect('/login')


class CriarAluno(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            materias = Materia.query()
            page = {"tipo": 1, "materias": materias}
            self.render("criaraluno.html", page=page)
        else:
            self.redirect('/login')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            matricula = self.request.get('matricula')
            periodo = self.request.get('periodo')
            nome = self.request.get('nome')
            materias = self.request.get_all('mat')
            if materias:
                materias = list(map(int, materias))
            aluno = Aluno(matricula=matricula, periodo=periodo, nome=nome, materias=materias, id=int(matricula), user_id=int(matricula))
            aluno.put()
            time.sleep(.1)
            self.redirect("/listaralunos")
        else:
            self.redirect('/login')


class CriarMateria(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            formularios = Formulario.query()
            page = {"tipo": 1, "formularios": formularios}
            self.render("criarmateria.html", page=page)
        else:
            self.redirect('/login')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            titulo = self.request.get('titulo')
            professor = self.request.get('professor')
            periodo = self.request.get('periodo')
            formularios = self.request.get_all('form')
            if formularios:
                formularios = list(map(int, formularios))
            cont = ndb.Key(Contador, 1).get()
            if not cont:
                cont = Contador(id_formularios=1, id_perguntas=1, id_materias=1, id=1)
            materia = Materia(titulo=titulo, professor=professor, periodo=periodo, formularios=formularios, id=cont.id_materias, user_id=cont.id_materias)
            cont.id_materias += 1
            cont.put()
            materia.put()
            time.sleep(.1)
            self.redirect("/listarmaterias")
        else:
            self.redirect('/login')


class CriarPergunta(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            self.render("criarpergunta.html")
        else:
            self.redirect('/login')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            enunciado = self.request.get('enunciado')
            tipo = int(self.request.get('tipo'))
            respostas = self.request.get_all('resposta')
            cont = ndb.Key(Contador, 1).get()
            if not cont:
                cont = Contador(id_formularios=1, id_perguntas=1, id_materias=1, id=1)
            perg = Pergunta(tipo=tipo, enunciado=enunciado, respostas=respostas, id=cont.id_perguntas, user_id=cont.id_perguntas)
            cont.id_perguntas += 1
            cont.put()
            perg.put()
            time.sleep(.1)
            self.redirect('/listarperguntas')
        else:
            self.redirect('/login')


class ApagarFormulario(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = int(self.request.get('id'))
            form = ndb.Key(Formulario, id).get()
            form.key.delete()
            time.sleep(.1)
            self.redirect('/listarformularios')
        else:
            self.redirect('/login')


class ApagarPergunta(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = int(self.request.get('id'))
            perg = ndb.Key(Pergunta, id).get()
            perg.key.delete()
            time.sleep(.1)
            self.redirect('/listarperguntas')
        else:
            self.redirect('/login')


class ApagarMateria(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = int(self.request.get('id'))
            mat = ndb.Key(Materia, id).get()
            mat.key.delete()
            time.sleep(.1)
            self.redirect('/listarmaterias')
        else:
            self.redirect('/login')


class ApagarAluno(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = int(self.request.get('id'))
            aluno = ndb.Key(Aluno, id).get()
            aluno.key.delete()
            time.sleep(.1)
            self.redirect('/listaralunos')
        else:
            self.redirect('/login')


class EditarFormulario(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = int(self.request.get('id'))
            form = ndb.Key(Formulario, id).get()
            perguntas = Pergunta.query()
            perguntasnt = []
            perguntast = []
            for perg in perguntas:
                if perg.user_id in form.perguntas:
                    perguntast.append(perg)
                else:
                    perguntasnt.append(perg)
            page = {
                "tipo": 2,
                "formulario": form,
                "perguntast": perguntast,
                "perguntasnt": perguntasnt
            }
            data["formulario"] = id
            DATA_COOKIE[cookie] = data
            self.render("criarformulario.html", page=page)
        else:
            self.redirect('/login')
    
    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = data["formulario"]
            titulo = self.request.get('titulo')
            descricao = self.request.get('descricao')
            perguntas = self.request.get_all('perg')
            if perguntas:
                perguntas = list(map(int, perguntas))
            form = ndb.Key(Formulario, id).get()
            form.titulo = titulo
            form.descricao = descricao
            form.perguntas = perguntas
            form.put()
            time.sleep(.1)
            data["formulario"] = None
            DATA_COOKIE[cookie] = data
            self.redirect('/listarformularios')
        else:
            self.redirect('/login')


class EditarAluno(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = int(self.request.get('id'))
            aluno = ndb.Key(Aluno, id).get()
            materias = Materia.query()
            materiast = []
            materiasnt = []
            for mat in materias:
                if mat.user_id in aluno.materias:
                    materiast.append(mat)
                else:
                    materiasnt.append(mat)
            page = {
                "tipo": 2,
                "aluno": aluno,
                "materiast": materiast,
                "materiasnt": materiasnt
            }
            data["aluno"] = id
            DATA_COOKIE[cookie] = data
            self.render("criaraluno.html", page=page)
        else:
            self.redirect('/login')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = data["aluno"]
            matricula = self.request.get('matricula')
            periodo = self.request.get('periodo')
            nome = self.request.get('nome')
            materias = self.request.get_all('mat')
            if materias:
                materias = list(map(int, materias))
            aluno = ndb.Key(Aluno, id).get()
            aluno.key.delete()
            aluno = Aluno(matricula=matricula, periodo=periodo, nome=nome, materias=materias, id=int(matricula), user_id=int(matricula))
            aluno.put()
            time.sleep(.1)
            data["aluno"] = None
            DATA_COOKIE[cookie] = data
            self.redirect('/listaralunos')
        else:
            self.redirect('/login')


class EditarMateria(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = int(self.request.get('id'))
            mat = ndb.Key(Materia, id).get()
            formularios = Formulario.query()
            formulariost = []
            formulariosnt = []
            for form in formularios:
                if form.user_id in mat.formularios:
                    formulariost.append(form)
                else:
                    formulariosnt.append(form)
            page = {
                "tipo": 2,
                "materia": mat,
                "formulariost": formulariost,
                "formulariosnt": formulariosnt
            }
            data["materia"] = id
            DATA_COOKIE[cookie] = data
            self.render("criarmateria.html", page=page)
        else:
            self.redirect('/login')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = data["materia"]
            titulo = self.request.get('titulo')
            professor = self.request.get('professor')
            periodo = self.request.get('periodo')
            formularios = self.request.get_all('form')
            if formularios:
                formularios = list(map(int, formularios))
            mat = ndb.Key(Materia, id).get()
            mat.titulo = titulo
            mat.professor = professor
            mat.periodo = periodo
            mat.formularios = formularios
            mat.put()
            time.sleep(.1)
            data["materia"] = None
            DATA_COOKIE[cookie] = data
            self.redirect('/listarmaterias')
        else:
            self.redirect('/login')


class EditarPergunta(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = int(self.request.get('id'))
            perg = ndb.Key(Pergunta, id).get()
            data["pergunta"] = id
            DATA_COOKIE[cookie] = data
            self.render("editarpergunta.html", pergunta=perg)
        else:
            self.redirect('/login')
    
    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            id = data["pergunta"]
            perg = ndb.Key(Pergunta, id).get()
            enunciado = self.request.get('enunciado')
            tipo = int(self.request.get('tipo'))
            respostas = self.request.get_all('resposta')
            perg.tipo = tipo
            perg.enunciado = enunciado
            perg.respostas = respostas
            perg.put()
            time.sleep(.1)
            data["pergunta"] = None
            DATA_COOKIE[cookie] = data
            self.redirect('/listarperguntas')
        else:
            self.redirect('/login')


class Teste(Handler):
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data  = DATA_COOKIE.get(str(cookie),'')
        self.write(DATA_COOKIE)


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/aluno', AlunoHandler),
    ('/formularios', FormulariosHandler),
    ('/avaliar', AvaliacaoHandler),
    ('/professor', CodigoHandler),
    ('/login', LoginHandler),
    ('/admin', AdministradorHandler),
    ('/criarformulario', CriarFormulario),
    ('/criarmateria', CriarMateria),
    ('/criarpergunta', CriarPergunta),
    ('/criaraluno', CriarAluno),
    ('/listarformularios', ListarFormularios),
    ('/listarmaterias', ListarMaterias),
    ('/listaralunos', ListarAlunos),
    ('/listarperguntas', ListarPerguntas),
    ('/editarformulario', EditarFormulario),
    ('/editarmateria', EditarMateria),
    ('/editaraluno', EditarAluno),
    ('/editarpergunta', EditarPergunta),
    ('/apagarformulario', ApagarFormulario),
    ('/apagarpergunta', ApagarPergunta),
    ('/apagarmateria', ApagarMateria),
    ('/apagaraluno', ApagarAluno),
    ('/teste', Teste)
], debug=True)
