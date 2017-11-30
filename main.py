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


class LoginAlunoHandler(Handler):

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
                    'perm': 1,
                    'mat': matricula,
                    'form': None,
                    'materias': None,
                    'pergunta': None,
                    'progresso': None
                }
                DATA_COOKIE[cookie] = data
                self.response.set_cookie(key='__ck',value=cookie)
                self.redirect('/formularios')
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')


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
            if data and data['perm'] == 1:
                aluno = ndb.Key(Aluno, data['mat']).get()
                materias = Materia.query(Materia.user_id.IN(aluno.materias))
                form_pesquisa = []
                for materia in materias:
                    form_pesquisa += materia.formularios
                form_pesquisa = list(set(form_pesquisa))
                forms = Formulario.query(Formulario.user_id.IN(form_pesquisa))
                form = []
                for formu in forms:
                    progresso = Progresso.query(ndb.AND(Progresso.formulario == formu.user_id, Progresso.matricula == data['mat'])).fetch(keys_only=True)
                    if not progresso:
                        progresso = Progresso(matricula=data['mat'], formulario=formu.user_id, progresso=0)
                    else:
                        progresso = progresso.pop(0).get()
                    d = {
                        "titulo": formu.titulo,
                        "descricao": formu.descricao,
                        "codigo": formu.user_id,
                        "progresso": int((float(progresso.progresso)/len(formu.perguntas))*100)
                    }
                    progresso.put()
                    form.append(d)
                self.render("formularios.html", formularios=form)
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')

    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            form = self.request.get('form')
            if data and data['perm'] == 1 and form != '':
                form = int(form)
                materias = Materia.query(Materia.formularios.IN([form]))
                formulario = ndb.Key(Formulario, form).get()
                data['form'] = formulario
                data['materias'] = materias
                DATA_COOKIE[cookie] = data
                self.redirect('/avaliar')
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')


class AvaliacaoHandler(Handler):
    def get(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data and data['perm'] == 1 and data['form'] and data['materias']:
                formu = data['form']
                materias = data['materias']
                progresso = Progresso.query(ndb.AND(Progresso.formulario == formu.user_id, Progresso.matricula == data['mat'])).fetch(keys_only=True)
                progresso = progresso.pop(0).get()
                aluno = ndb.Key(Aluno, data['mat']).get()
                codigo = Codigo.query(ndb.AND(Codigo.formulario == formu.user_id, Codigo.nomeAluno == aluno.nome)).fetch(keys_only=True)
                if progresso.progresso != len(formu.perguntas) and (not codigo):
                    lista_perguntas = list(map(int, formu.perguntas))
                    pergunta = ndb.Key(Pergunta, lista_perguntas[progresso.progresso]).get()
                    page = {
                        "formulario": formu,
                        "numero": progresso.progresso,
                        "pergunta": pergunta,
                        "materias": materias
                    }
                    data['pergunta'] = pergunta
                    data['progresso'] = progresso
                    DATA_COOKIE[cookie] = data
                    self.render('questao.html', page=page)
                elif not codigo:
                    self.redirect('/points')
                else:
                    self.redirect('/formularios')
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')

    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data and data['perm'] == 1 and data['form'] and data['materias'] and data['pergunta'] and data['progresso']:
                formu = data['form']
                materias = data['materias']
                pergunta = data['pergunta']
                progresso = data['progresso']
                progresso.progresso += 1
                resultados = []
                for materia in materias:
                    resu = Resultado(materia=materia.titulo, enunciado=pergunta.enunciado, respostas = self.request.get_all(materia.titulo))
                    resultados.append(resu)
                progresso.put()
                ndb.put_multi(resultados)
                time.sleep(.2)
                self.redirect('/avaliar')
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')


class CodigoHandler(Handler):

    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['mat'] and data['perm'] == 1 and data['form']:
            aluno = ndb.Key(Aluno, data['mat']).get()
            form = data['form']
            progresso = Progresso.query(ndb.AND(Progresso.formulario == form.user_id, Progresso.matricula == data['mat'])).fetch(keys_only=True)
            progresso = progresso.pop(0).get()
            if progresso.progresso == len(form.perguntas):
                cont = ndb.Key(Contador, 1).get()
                cod = Codigo(nomeAluno=aluno.nome, periodo=aluno.periodo, formulario=form.user_id, codigo=str("GEST" + str(cont.maior_cod)))
                cont.maior_cod += 1
                cont.put()
                codigo = cod.codigo[:]
                cod.put()
                time.sleep(.1)
                self.render("gratificacao.html", codigo=codigo)
            else:
                self.redirect('/formularios')
        else:
            self.redirect('/')


class ProfessorHandler(Handler):
    def get(self):
        self.render("professor.html")
    
    def post(self):
        global DATA_COOKIE
        codigo = self.request.get('codigo')
        if codigo:
            codigos = Codigo.query(Codigo.codigo == codigo).fetch(keys_only=True)
            if codigos:
                cod = codigos.pop(0).get()
                cookie = gerador_cookie()
                data = {"codigo": cod}
                DATA_COOKIE[cookie] = data
                self.response.set_cookie(key='__pf', value=cookie)
                self.redirect('/validar')
            else:
                self.redirect('/professor')
        else:
            self.redirect('/professor')


class ValidarCodigo(Handler):

    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__pf')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['codigo']:
            cod = data['codigo']
            if cod:
                page = {
                    "codigo": cod
                }
                self.render("validar.html", page=page)
            else:
                self.redirect('/professor')
        else:
            self.redirect('/professor')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__pf')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['codigo']:
            cod = data['codigo']
            if cod:
                cod.key.delete()
                time.sleep(.1)
            self.redirect('/professor')
        else:
            self.redirect('/professor')


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
                "titulo": None,
                "subtitulo": None,
                "entidade": None,
                "objeto": None,
                "objects": "formulario",
                "objects_h": [],
                "objects_nh": formularios,
                "button": "criarformulario"
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
                "titulo": None,
                "subtitulo": None,
                "entidade": None,
                "objeto": None,
                "objects": "aluno",
                "objects_h": [],
                "objects_nh": alunos,
                "button": "criaraluno"
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
                "titulo": None,
                "subtitulo": None,
                "entidade": None,
                "objeto": None,
                "objects": "materia",
                "objects_h": [],
                "objects_nh": materias,
                "button": "criarmateria"
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
                "titulo": None,
                "subtitulo": None,
                "entidade": None,
                "objeto": None,
                "objects": "pergunta",
                "objects_h": [],
                "objects_nh": perguntas,
                "button": "criarpergunta"
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
                "titulo": u"Criar Formulário",
                "subtitulo": u"Formulário",
                "entidade": "formulario",
                "objeto": None,
                "objects": "pergunta",
                "objects_h": [],
                "objects_nh": perguntas,
                "url": "criarformulario",
                "button": None
            }
            self.render("entidades.html", page=page)
        else:
            self.redirect('/login')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['perm'] == 2:
            titulo = self.request.get('titulo')
            descricao = self.request.get('descricao')
            perguntas = self.request.get_all('pergunta')
            if perguntas:
                perguntas = list(map(int, perguntas))
            cont = ndb.Key(Contador, 1).get()
            if not cont:
                cont = Contador(id_formularios=1, id_perguntas=1, id_materias=1, maior_cod=1, id=1)
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
            page = {
                "titulo": "Criar Aluno",
                "subtitulo": "Aluno",
                "entidade": "aluno",
                "objeto": None,
                "objects": "materia",
                "objects_h": [],
                "objects_nh": materias,
                "url": "criaraluno",
                "button": None
            }
            self.render("entidades.html", page=page)
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
            materias = self.request.get_all('materia')
            if materias:
                materias = list(map(int, materias))
            aluno = Aluno(matricula=matricula, periodo=periodo, nome=nome, materias=materias, id=int(matricula), user_id=int(matricula))
            aluno.put()
            time.sleep(.2)
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
            page = {
                "titulo": u"Criar Matéria",
                "subtitulo": u"Matéria",
                "entidade": "materia",
                "objeto": None,
                "objects": "formulario",
                "objects_h": [],
                "objects_nh": formularios,
                "url": "criarmateria",
                "button": None
            }
            self.render("entidades.html", page=page)
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
            formularios = self.request.get_all('formulario')
            if formularios:
                formularios = list(map(int, formularios))
            cont = ndb.Key(Contador, 1).get()
            if not cont:
                cont = Contador(id_formularios=1, id_perguntas=1, id_materias=1, maior_cod=1, id=1)
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
                cont = Contador(id_formularios=1, id_perguntas=1, id_materias=1, maior_cod=1, id=1)
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
            time.sleep(.2)
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
                "titulo": u"Editar Formulário",
                "subtitulo": u"Formulário",
                "entidade": "formulario",
                "objeto": form,
                "objects": "pergunta",
                "objects_h": perguntast,
                "objects_nh": perguntasnt,
                "url": "editarformulario",
                "button": None
            }
            data["formulario"] = id
            DATA_COOKIE[cookie] = data
            self.render("entidades.html", page=page)
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
            perguntas = self.request.get_all('pergunta')
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
                "titulo": "Editar Aluno",
                "subtitulo": "Aluno",
                "entidade": "aluno",
                "objeto": aluno,
                "objects": "materia",
                "objects_h": materiast,
                "objects_nh": materiasnt,
                "url": "editaraluno",
                "button": None
            }
            data["aluno"] = id
            DATA_COOKIE[cookie] = data
            self.render("entidades.html", page=page)
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
            materias = self.request.get_all('materia')
            if materias:
                materias = list(map(int, materias))
            aluno = ndb.Key(Aluno, id).get()
            aluno.key.delete()
            aluno = Aluno(
                matricula=matricula,
                periodo=periodo,
                nome=nome,
                materias=materias,
                id=int(matricula),
                user_id=int(matricula)
            )
            aluno.put()
            time.sleep(.2)
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
                "titulo": u"Editar Matéria",
                "subtitulo": u"Matéria",
                "entidade": "materia",
                "objeto": mat,
                "objects": "formulario",
                "objects_h": formulariost,
                "objects_nh": formulariosnt,
                "url": "editarmateria",
                "button": None
            }
            data["materia"] = id
            DATA_COOKIE[cookie] = data
            self.render("entidades.html", page=page)
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
            formularios = self.request.get_all('formulario')
            if formularios:
                formularios = list(map(int, formularios))
            mat = ndb.Key(Materia, id).get()
            mat.titulo = titulo
            mat.professor = professor
            mat.periodo = periodo
            mat.formularios = formularios
            mat.put()
            time.sleep(.2)
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


app = webapp2.WSGIApplication([
    # ('/', MainHandler),
    ('/', LoginAlunoHandler),
    ('/formularios', FormulariosHandler),
    ('/avaliar', AvaliacaoHandler),
    ('/points', CodigoHandler),
    ('/login', LoginHandler),
    ('/professor', ProfessorHandler),
    ('/validar', ValidarCodigo),
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
    ('/apagaraluno', ApagarAluno)
], debug=True)
