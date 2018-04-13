#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import re
import time
import urllib
from datetime import datetime
from hashlib import sha224
from os.path import dirname, join

import jinja2
import webapp2
from webapp2 import Route

from google.appengine.ext import ndb
from models import *

TEMPLATE_DIR = join(dirname(__file__), "templates")
# DATA_DIR = join(dirname(__file__), "data")
# GESTAO_COMERCIAL_DATA = json.loads(open(join(
#     DATA_DIR, "gestao_comercial.json")).read())

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR), autoescape=True)
# GESTAO_COMERCIAL_HTML = JINJA_ENV.get_template(
#     "index.html").render(curso=GESTAO_COMERCIAL_DATA)


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

    def json_encode(self, o):
        self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
        query = o.query()
        query_dict = [
            dict(q.to_dict(),
            **dict(id=q.key.id()))
            for q in query]
        self.write(json.dumps(query_dict))
    
    def getTipo(self, tipo):
        if tipo == "texto":
            return 1
        elif tipo == "radio":
            return 2
        elif tipo == "marcar":
            return 3
    
    def getAvaliado(self, avaliado):
        if avaliado == "materias":
            return 1
        elif avaliado == "outros":
            return 2


class LoginAlunoHandler(Handler):

    def get(self):
        self.render("Aluno/loginaluno.html")

    def post(self):
        global DATA_COOKIE
        try:
            matricula = self.request.get('mat')
            # aluno = ndb.Key(Aluno, matricula).get()
            aluno = Aluno.query_aluno(matricula)
            if aluno and matricula == aluno.matricula :
                cookie = gerador_cookie()
                data = {
                    'user': aluno,
                    'perm': 1
                }
                DATA_COOKIE[cookie] = data
                self.response.set_cookie(key='__ck', value=cookie)
                self.redirect('/alunos/formularios')
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')


class LoginHandler(Handler):

    def get(self):
        self.render("Admin/loginadmin.html")

    def post(self):
        global DATA_COOKIE
        try:
            usuario = self.request.get('usuario')
            senha = self.request.get('senha')
            if usuario == "a" and senha == "a":
                cookie = gerador_cookie()
                data = {
                    "perm": 2
                }
                DATA_COOKIE[cookie] = data
                self.response.set_cookie(key='__ck', value=cookie)
                self.redirect('/admin')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')


class AvaliacaoHandler(Handler):
    
    def get(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 1 and data.get('user', ''):
                user = data['user']
                turma = Turma.query(
                    Turma.alunos.IN(
                        [user.key.id()]
                    )
                )
                page = []
                if turma.count():
                    progs = Progresso.query(
                        Progresso.user_id == user.key.id()
                    )
                    formularios = Formulario.query(
                        Formulario.turmas.IN(
                            [ tur.key.id() for tur in turma]
                        )
                    )
                    for form in formularios:
                        prog = progs.filter(
                            ndb.AND(
                                Progresso.formulario == form.key.id()
                            )
                        ).get()
                        if prog:
                            prog = int((float(prog.progresso)/len(form.perguntas))*100.0)
                        else:
                            prog = 0
                        page.append((form, prog))
                    data['turma'] = turma.get()
                    DATA_COOKIE[cookie] = data
                self.render('Aluno/formularios.html', page=page)
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')


class HandlerForm(Handler):
    
    def get(self, formulario):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 1 and data.get('user', ''):
                user = data['user']
                form = ndb.Key(Formulario, int(formulario)).get()
                data['form'] = form
                DATA_COOKIE[cookie] = data
                if form:
                    prog = Progresso.query(ndb.AND(
                        Progresso.user_id == user.key.id(),
                        Progresso.formulario == form.key.id()
                    )).get()
                    pergunta = None
                    if prog:
                        if prog.progresso < len(form.perguntas):
                            pergunta = form.perguntas[prog.progresso]
                        else:
                            self.redirect("/alunos/formularios")
                    else:
                        pergunta = form.perguntas[0]
                    self.redirect('/alunos/pergunta/%d' % (int(pergunta)))
                else:
                    self.redirect('/')
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')


class AvaliacaoPerguntaHandler(Handler):
    
    def get(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 1 and data.get('user', '') and data.get('turma', '') and data.get('form', ''):
                turma = data['turma']
                form = data['form']
                pergunta = ndb.Key(Pergunta, int(id)).get()
                materias = []
                if pergunta.avaliado == 1:
                    if data.get('materias', ''):
                        materias = data['materias']
                    else:
                        materias = ndb.get_multi(
                            [ndb.Key(Materia, int(k)) for k in turma.materias]
                        )
                        data['materias'] = materias
                page = {
                    "pergunta": pergunta,
                    "materias": materias,
                    "formulario": form
                }
                self.render('Aluno/questao.html', page=page)
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')
        
    def post(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 1 and data.get('user', '') and data.get('turma', '') and data.get('form', ''):
                user = data['user']
                turma = data['turma']
                formulario = data['form']
                pergunta = ndb.Key(Pergunta, int(id)).get()
                curso = ndb.Key(Curso, int(turma.id_curso)).get()
                res = []
                if pergunta.avaliado == 1:
                    if data.get('materias', ''):
                        materias = data['materias']
                    else:
                        materias = ndb.get_multi(
                            [ndb.Key(Materia, int(k)) for k in turma.materias]
                        )
                        data['materias'] = materias
                    if materias:
                        for materia in materias:
                            res.append(
                                Resultado(
                                    id_curso=turma.id_curso,
                                    id_aluno=user.key.id(),
                                    matricula_aluno=user.matricula,
                                    id_formulario=formulario.key.id(),
                                    id_pergunta=pergunta.key.id(),
                                    titulo_formulario=formulario.titulo,
                                    enunciado=pergunta.enunciado,
                                    respostas=self.request.get_all(materia.titulo),
                                    periodo=user.periodo,
                                    avaliado=materia.titulo,
                                    nome_curso=curso.nome
                                )
                            )
                else:
                    res.append(
                        Resultado(
                            id_curso=turma.id_curso,
                            id_aluno=user.key.id(),
                            matricula_aluno=user.matricula,
                            id_formulario=formulario.key.id(),
                            id_pergunta=pergunta.key.id(),
                            titulo_formulario=formulario.titulo,
                            enunciado=pergunta.enunciado,
                            respostas=self.request.get_all('outros'),
                            periodo=user.periodo,
                            avaliado='outros',
                            nome_curso=curso.nome
                        )
                    )
                prog = Progresso.query(ndb.AND(
                        Progresso.user_id == user.key.id(),
                        Progresso.formulario == formulario.key.id()
                    )).get()
                if prog:
                    prog.progresso += 1
                else:
                    prog = Progresso(
                        user_id=user.key.id(),
                        matricula=user.matricula,
                        formulario=formulario.key.id(),
                        progresso=1
                    )
                ndb.put_multi(res)
                prog.put()
                time.sleep(.1)
                if len(formulario.perguntas) > prog.progresso:
                    self.redirect('/alunos/pergunta/%d' % (
                        int(formulario.perguntas[prog.progresso])))
                else:
                    self.redirect('/alunos/points')
            else:
                self.redirect('/')
        except ValueError:
            self.redirect('/')


class CodigoHandler(Handler):

    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['user'] and data['perm'] == 1 and data['form']:
            aluno = data['user']
            form = data['form']
            progresso = Progresso.query(
                ndb.AND(
                    Progresso.formulario == form.key.id(),
                    Progresso.user_id == aluno.key.id()
                )
            ).fetch(keys_only=True)
            progresso = progresso.pop(0).get()
            if progresso.progresso == len(form.perguntas):
                cont = Contador.query(Contador.user_id == 1).get()
                cod = Codigo(
                    id_aluno=aluno.key.id(),
                    nomeAluno=aluno.nome,
                    periodo=aluno.periodo,
                    id_formulario=form.key.id(),
                    codigo=str("COD" + str(cont.maior_cod))
                )
                cont.maior_cod += 1
                codigo = cod.codigo[:]
                cod.put()
                cont.put()
                time.sleep(.1)
                self.render("Aluno/gratificacao.html", codigo=codigo)
            else:
                self.redirect('/alunos/formularios')
        else:
            self.redirect('/')


class ProfessorHandler(Handler):
    
    def get(self):
        self.render("Prof/professor.html")
    
    def post(self):
        global DATA_COOKIE
        codigo = self.request.get('codigo')
        if codigo:
            codigos = Codigo.query(
                Codigo.codigo == codigo
            ).fetch(keys_only=True)
            if codigos:
                cod = codigos.pop(0).get()
                cookie = gerador_cookie()
                data = {
                    "codigo": cod,
                    'perm': 3
                }
                DATA_COOKIE[cookie] = data
                self.response.set_cookie(key='__ck', value=cookie)
                self.redirect('/validar')
            else:
                self.redirect('/professor')
        else:
            self.redirect('/professor')


class ValidarCodigo(Handler):

    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data.get('codigo','') != '' and data.get('perm','') == 3:
            cod = data['codigo']
            if cod:
                self.render("Prof/validar.html", codigo=cod)
            else:
                self.redirect('/professor')
        else:
            self.redirect('/professor')

    def post(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data and data['codigo'] and data.get('perm','') == 3:
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
            self.render("Admin/administrador.html")
        else:
            self.redirect('/login')


class FormularioHandler(Handler):
    def list_ents(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/listar_formularios.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
            
    
    def list(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.json_encode(Formulario)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/criarformulario.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                titulo = self.request.get('titulo')
                descricao = self.request.get('descricao')
                pergunta = self.request.get_all('pergunta')
                turmas = self.request.get_all('turma')
                if pergunta:
                    pergunta = list(map(int, pergunta))
                if turmas:
                    turmas = list(map(int, turmas))
                contador = Contador.query(Contador.user_id == 1).get()
                if not contador:
                    contador = Contador()
                form = Formulario(
                    user_id=contador.id_formularios,
                    titulo=titulo,
                    descricao=descricao,
                    perguntas=pergunta,
                    turmas=turmas
                )
                contador.id_formularios += 1
                contador.put()
                form.put()
                time.sleep(.1)
                self.redirect('/admin/formularios')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view_update(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                form = ndb.Key(Formulario, int(id)).get()
                perguntas = Pergunta.query()
                pergsatuais = []
                pergsoutros = []
                for pergunta in perguntas:
                    if pergunta.key.id() in form.perguntas:
                        pergsatuais.append(pergunta)
                    else:
                        pergsoutros.append(pergunta)
                
                turmas = Turma.query()
                turmasatuais = []
                turmasoutros = []
                for turma in turmas:
                    if turma.key.id() in form.turmas:
                        turmasatuais.append(turma)
                    else:
                        turmasoutros.append(turma)
                page = {
                    "formulario": form,
                    "turmas":{
                        "atuais": turmasatuais,
                        "outras": turmasoutros
                    },
                    "perguntas":{
                        "atuais": pergsatuais,
                        "outras": pergsoutros
                    }
                }
                self.render("Admin/editarformulario.html", page=page)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def put(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                titulo = self.request.get('titulo')
                descricao = self.request.get('descricao')
                pergunta = self.request.get_all('pergunta')
                turmas = self.request.get_all('turma')
                if pergunta:
                    pergunta = list(map(int, pergunta))
                if turmas:
                    turmas = list(map(int, turmas))
                form = ndb.Key(Formulario, int(id)).get()
                form.titulo = titulo
                form.descricao = descricao
                form.perguntas = pergunta
                form.turmas = turmas
                form.put()
                time.sleep(.1)
                self.redirect('/admin/formularios')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')

    def delete(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                ndb.Key(Formulario, int(id)).delete()
                time.sleep(.1)
                self.redirect('/admin/formularios')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')


class PerguntaHandler(Handler):
    def list_ents(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/listar_perguntas.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def list(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.json_encode(Pergunta)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/criarpergunta.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                enunciado = self.request.get('enunciado')
                tipo = self.request.get('tipo')
                respostas = self.request.get_all('resposta')
                avaliado = self.request.get('avaliado')
                contador = Contador.query(Contador.user_id == 1).get()
                if not contador:
                    contador = Contador()
                perg = Pergunta(
                    user_id=contador.id_perguntas,
                    avaliado=self.getAvaliado(avaliado),
                    tipo=self.getTipo(tipo),
                    enunciado=enunciado,
                    respostas=respostas
                )
                contador.id_perguntas +=1
                contador.put()
                perg.put()
                time.sleep(.1)
                self.redirect('/admin/perguntas')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view_update(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                perg = ndb.Key(Pergunta, int(id)).get()
                page = {
                    "pergunta": perg
                }
                self.render("Admin/editarpergunta.html", page=page)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def put(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                enunciado = self.request.get('enunciado')
                tipo = self.request.get('tipo')
                respostas = self.request.get_all('resposta')
                avaliado = self.request.get('avaliado')
                perg = ndb.Key(Pergunta, int(id)).get()
                perg.tipo = self.getTipo(tipo)
                perg.avaliado = avaliado
                perg.enunciado = enunciado
                perg.respostas = respostas
                perg.put()
                time.sleep(.1)
                self.redirect('/admin/perguntas')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')

    def delete(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                ndb.Key(Pergunta, int(id)).delete()
                time.sleep(.1)
                self.redirect('/admin/perguntas')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')


class MateriaHandler(Handler):
    def list_ents(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/listar_materias.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def list(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.json_encode(Materia)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/criarmateria.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                titulo = self.request.get('titulo')
                professor = self.request.get('professor')
                periodo = self.request.get('periodo')
                contador = Contador.query(Contador.user_id == 1).get()
                if not contador:
                    contador = Contador()
                materia = Materia(
                    user_id=contador.id_materias,
                    titulo=titulo,
                    professor=professor,
                    periodo=periodo,
                )
                contador.id_materias += 1
                contador.put()
                materia.put()
                time.sleep(.1)
                self.redirect('/admin/materias')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view_update(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                mat = ndb.Key(Materia, int(id)).get()
                page = {
                    "materia": mat
                }
                self.render("Admin/editarmateria.html", page=page)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def put(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                titulo = self.request.get('titulo')
                professor = self.request.get('professor')
                periodo = self.request.get('periodo')
                mat = ndb.Key(Materia, int(id)).get()
                mat.titulo = titulo
                mat.professor = professor
                mat.periodo = periodo
                mat.put()
                time.sleep(.1)
                self.redirect('/admin/materias')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')

    def delete(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                ndb.Key(Materia, int(id)).delete()
                time.sleep(.1)
                self.redirect('/admin/materias')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')


class AlunoHandler(Handler):
    def list_ents(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/listar_alunos.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def list(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.json_encode(Aluno)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/criaraluno.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                matricula = self.request.get('matricula')
                periodo = self.request.get('periodo')
                nome = self.request.get('nome')
                aluno = Aluno(
                    matricula=matricula,
                    periodo=periodo,
                    nome=nome
                )
                aluno.put()
                time.sleep(.1)
                self.redirect('/admin/alunos')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view_update(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                aluno = ndb.Key(Aluno, int(id)).get()
                page = {
                    "aluno": aluno
                }
                self.render("Admin/editaraluno.html", page=page)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def put(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                matricula = self.request.get('matricula')
                periodo = self.request.get('periodo')
                nome = self.request.get('nome')
                aluno = ndb.Key(Aluno, int(id)).get()
                aluno.matricula = matricula
                aluno.periodo = periodo
                aluno.nome = nome
                aluno.put()
                time.sleep(.1)
                self.redirect('/admin/alunos')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')

    def delete(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                ndb.Key(Aluno, int(id)).delete()
                time.sleep(.1)
                self.redirect('/admin/alunos')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')


class TurmaHandler(Handler):
    def list_ents(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/listar_turmas.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def list(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.json_encode(Turma)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/criarturma.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                periodo = self.request.get('periodo')
                cursos = self.request.get('curso')
                alunos = self.request.get_all('aluno')
                materias = self.request.get_all('materia')
                contador = Contador.query(Contador.user_id == 1).get()
                if cursos:
                    cursos = int(cursos)
                else:
                    cursos = None
                if alunos:
                    alunos = list(map(int, alunos))
                if materias:
                    materias = list(map(int, materias))
                if not contador:
                    contador = Contador()
                turma = Turma(
                    id_curso=cursos,
                    user_id=contador.id_turmas,
                    periodo = periodo,
                    alunos = alunos,
                    materias = materias
                )
                contador.id_turmas +=1
                contador.put()
                turma.put()
                time.sleep(.1)
                self.redirect('/admin/turmas')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view_update(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                turma = ndb.Key(Turma, int(id)).get()
                alunos = Aluno.query()
                materias = Materia.query()
                cursos = Curso.query()
                alunosatuais = []
                alunosoutros = []
                for aluno in alunos:
                    if aluno.key.id() in turma.alunos:
                        alunosatuais.append(aluno)
                    else:
                        alunosoutros.append(aluno)
                
                matsatuais = []
                matsoutros = []
                for materia in materias:
                    if materia.key.id() in turma.materias:
                        matsatuais.append(materia)
                    else:
                        matsoutros.append(materia)
                
                cursoatuais = []
                cursooutros = []
                for curso in cursos:
                    if curso.key.id() == turma.id_curso:
                        cursoatuais.append(curso)
                    else:
                        cursooutros.append(curso)
                
                page = {
                    "turma": turma,
                    "cursos":{
                        "atuais": cursoatuais,
                        "outras": cursooutros
                    },
                    "alunos":{
                        "atuais": alunosatuais,
                        "outras": alunosoutros
                    },
                    "materias":{
                        "atuais": matsatuais,
                        "outras": matsoutros
                    }
                }
                self.render("Admin/editarturma.html", page=page)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def put(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                periodo = self.request.get('periodo')
                cursos = self.request.get('curso')
                alunos = self.request.get_all('aluno')
                materias = self.request.get_all('materia')
                if alunos:
                    alunos = list(map(int, alunos))
                if materias:
                    materias = list(map(int, materias))
                if cursos:
                    cursos = int(cursos)
                else:
                    cursos = None
                turma = ndb.Key(Turma, int(id)).get()
                turma.id_curso = cursos
                turma.periodo = periodo
                turma.alunos = alunos
                turma.materias = materias
                turma.put()
                time.sleep(.1)
                self.redirect('/admin/turmas')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')

    def delete(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                ndb.Key(Turma, int(id)).delete()
                time.sleep(.1)
                self.redirect('/admin/turmas')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')


class RelatorioHandler(Handler):

    def list_ents(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                forms = Formulario.query()
                page ={
                    "formularios": forms
                }
                self.render("Admin/listar_relatorio.html",page=page)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def list(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                query = Resultado.query(
                    Resultado.id_formulario == int(id)
                    )
                enunciados = []
                query_dict = []
                for q in query:
                    query_dict.append(
                        dict(
                            q.to_dict(),
                            **dict(id=q.key.id())
                        )
                    )
                    if q.enunciado not in enunciados:
                        enunciados.append(q.enunciado)
                enunciados.sort()
                from operator import itemgetter
                query_dict.sort(key=itemgetter('matricula_aluno', 'enunciado'))
                self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
                pa = {
                    "resultados":json.dumps(query_dict),
                    "enunciados":json.dumps(enunciados)
                }
                self.write(json.dumps(pa))
            else:
                self.redirect('/login')

        except ValueError:
            self.redirect('/login')
    

class LogoutHandler(Handler):
    
    def get(self):
        global DATA_COOKIE
        cookie = self.request.cookies.get('__ck')
        data = DATA_COOKIE.get(cookie, '')
        if data:
            DATA_COOKIE.pop(cookie, None)
        self.redirect('/')


class CursoHandler(Handler):
    def list_ents(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/listar_cursos.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
            
    
    def list(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.json_encode(Curso)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                self.render("Admin/criarcurso.html")
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def post(self):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                nome = self.request.get('nome')
                descricao = self.request.get('descricao')
                contador = Contador.query(Contador.user_id == 1).get()
                if not contador:
                    contador = Contador()
                curso = Curso(
                    cod=contador.id_cursos,
                    nome=nome,
                    descricao=descricao,
                )
                contador.id_cursos += 1
                contador.put()
                curso.put()
                time.sleep(.1)
                self.redirect('/admin/cursos')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def view_update(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                curso = ndb.Key(Curso, int(id)).get()
                page = {
                    "curso": curso
                }
                self.render("Admin/editarcurso.html", page=page)
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')
    
    def put(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                nome = self.request.get('nome')
                descricao = self.request.get('descricao')
                
                curso = ndb.Key(Curso, int(id)).get()
                curso.nome = nome
                curso.descricao = descricao
                curso.put()
                time.sleep(.1)
                self.redirect('/admin/cursos')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')

    def delete(self, id):
        global DATA_COOKIE
        try:
            cookie = self.request.cookies.get('__ck')
            data = DATA_COOKIE.get(cookie, '')
            if data != '' and data.get('perm', '') == 2:
                ndb.Key(Curso, int(id)).delete()
                time.sleep(.1)
                self.redirect('/admin/cursos')
            else:
                self.redirect('/login')
        except ValueError:
            self.redirect('/login')


class NotFoundPageHandler(Handler):
    def get(self):
        self.redirect('/')

app = webapp2.WSGIApplication([
    ('/logout', LogoutHandler),
    ('/', LoginAlunoHandler),
    ('/login', LoginHandler),
    ('/professor', ProfessorHandler),
    ('/alunos/formularios', AvaliacaoHandler),
    ('/alunos/points', CodigoHandler),
    ('/validar', ValidarCodigo),
    ('/admin', AdministradorHandler),
    Route(
        name='avalicsdafaohandler.get',
        template=r'/alunos/formularios/<formulario:(\d+)>',
        methods='GET',
        handler=HandlerForm,
        handler_method='get'
    ),
    Route(
        name='avalicaohandler.get',
        template=r'/alunos/pergunta/<id:(\d+)>',
        methods='GET',
        handler=AvaliacaoPerguntaHandler,
        handler_method='get'
    ),
    Route(
        name='avalicaohandler.post',
        template=r'/alunos/pergunta/<id:(\d+)>',
        methods='POST',
        handler=AvaliacaoPerguntaHandler,
        handler_method='post'
    ),
    Route(
        name='formhandler.list_ents',
        template=r'/admin/formularios',
        methods='GET',
        handler=FormularioHandler,
        handler_method='list_ents'
    ),
    Route(
        name='formhandler.list',
        template=r'/formularios',
        methods='GET',
        handler=FormularioHandler,
        handler_method='list'
    ),
    Route(
        name='formhandler.view',
        template=r'/formulario/view_criar',
        methods=None,
        handler=FormularioHandler,
        handler_method='view'
    ),
    Route(
        name='formhandler.post',
        template=r'/formulario/criar',
        methods=None,
        handler=FormularioHandler,
        handler_method='post'
    ),
    Route(
        name='formhandler.view_update',
        template=r'/formulario/<id:(\d+)>/view_atualizar',
        methods=None,
        handler=FormularioHandler,
        handler_method='view_update'
    ),
    Route(
        name='formhandler.put',
        template=r'/formulario/<id:(\d+)>/atualizar',
        methods=None,
        handler=FormularioHandler,
        handler_method='put'
    ),
    Route(
        name='formhandler.delete',
        template=r'/formulario/<id:(\d+)>/apagar',
        methods=None,
        handler=FormularioHandler,
        handler_method='delete'
    ),
    Route(
        name='perghandler.list_ents',
        template=r'/admin/perguntas',
        methods='GET',
        handler=PerguntaHandler,
        handler_method='list_ents'
    ),
    Route(
        name='perghandler.list',
        template=r'/perguntas',
        methods='GET',
        handler=PerguntaHandler,
        handler_method='list'
    ),
    Route(
        name='perghandler.view',
        template=r'/pergunta/view_criar',
        methods=None,
        handler=PerguntaHandler,
        handler_method='view'
    ),
    Route(
        name='perghandler.post',
        template=r'/pergunta/criar',
        methods=None,
        handler=PerguntaHandler,
        handler_method='post'
    ),
    Route(
        name='perghandler.view_update',
        template=r'/pergunta/<id:(\d+)>/view_atualizar',
        methods=None,
        handler=PerguntaHandler,
        handler_method='view_update'
    ),
    Route(
        name='perghandler.put',
        template=r'/pergunta/<id:(\d+)>/atualizar',
        methods=None,
        handler=PerguntaHandler,
        handler_method='put'
    ),
    Route(
        name='perghandler.delete',
        template=r'/pergunta/<id:(\d+)>/apagar',
        methods=None,
        handler=PerguntaHandler,
        handler_method='delete'
    ),
    Route(
        name='mathandler.list_ents',
        template=r'/admin/materias',
        methods='GET',
        handler=MateriaHandler,
        handler_method='list_ents'
    ),
    Route(
        name='mathandler.list',
        template=r'/materias',
        methods='GET',
        handler=MateriaHandler,
        handler_method='list'
    ),
    Route(
        name='mathandler.view',
        template=r'/materia/view_criar',
        methods=None,
        handler=MateriaHandler,
        handler_method='view'
    ),
    Route(
        name='mathandler.post',
        template=r'/materia/criar',
        methods=None,
        handler=MateriaHandler,
        handler_method='post'
    ),
    Route(
        name='mathandler.view_update',
        template=r'/materia/<id:(\d+)>/view_atualizar',
        methods=None,
        handler=MateriaHandler,
        handler_method='view_update'
    ),
    Route(
        name='mathandler.put',
        template=r'/materia/<id:(\d+)>/atualizar',
        methods=None,
        handler=MateriaHandler,
        handler_method='put'
    ),
    Route(
        name='mathandler.delete',
        template=r'/materia/<id:(\d+)>/apagar',
        methods=None,
        handler=MateriaHandler,
        handler_method='delete'
    ),
    Route(
        name='aluhandler.list_ents',
        template=r'/admin/alunos',
        methods='GET',
        handler=AlunoHandler,
        handler_method='list_ents'
    ),
    Route(
        name='aluhandler.list',
        template=r'/alunos',
        methods='GET',
        handler=AlunoHandler,
        handler_method='list'
    ),
    Route(
        name='aluhandler.view',
        template=r'/aluno/view_criar',
        methods=None,
        handler=AlunoHandler,
        handler_method='view'
    ),
    Route(
        name='aluhandler.post',
        template=r'/aluno/criar',
        methods=None,
        handler=AlunoHandler,
        handler_method='post'
    ),
    Route(
        name='aluhandler.view_update',
        template=r'/aluno/<id:(\d+)>/view_atualizar',
        methods=None,
        handler=AlunoHandler,
        handler_method='view_update'
    ),
    Route(
        name='aluhandler.put',
        template=r'/aluno/<id:(\d+)>/atualizar',
        methods=None,
        handler=AlunoHandler,
        handler_method='put'
    ),
    Route(
        name='aluhandler.delete',
        template=r'/aluno/<id:(\d+)>/apagar',
        methods=None,
        handler=AlunoHandler,
        handler_method='delete'
    ),
    Route(
        name='turmahandler.list_ents',
        template=r'/admin/turmas',
        methods='GET',
        handler=TurmaHandler,
        handler_method='list_ents'
    ),
    Route(
        name='turmahandler.list',
        template=r'/turmas',
        methods='GET',
        handler=TurmaHandler,
        handler_method='list'
    ),
    Route(
        name='turmahandler.view',
        template=r'/turma/view_criar',
        methods=None,
        handler=TurmaHandler,
        handler_method='view'
    ),
    Route(
        name='turmahandler.post',
        template=r'/turma/criar',
        methods=None,
        handler=TurmaHandler,
        handler_method='post'
    ),
    Route(
        name='turmahandler.view_update',
        template=r'/turma/<id:(\d+)>/view_atualizar',
        methods=None,
        handler=TurmaHandler,
        handler_method='view_update'
    ),
    Route(
        name='turmahandler.put',
        template=r'/turma/<id:(\d+)>/atualizar',
        methods=None,
        handler=TurmaHandler,
        handler_method='put'
    ),
    Route(
        name='turmahandler.delete',
        template=r'/turma/<id:(\d+)>/apagar',
        methods=None,
        handler=TurmaHandler,
        handler_method='delete'
    ),
    Route(
        name='resulthandler.list_ents',
        template=r'/admin/resultados',
        methods='GET',
        handler=RelatorioHandler,
        handler_method='list_ents'
    ),
    Route(
        name='resulthandler.list',
        template=r'/resultados/<id:(\d+)>',
        methods='GET',
        handler=RelatorioHandler,
        handler_method='list'
    ),
    Route(
        name='cursohandler.list_ents',
        template=r'/admin/cursos',
        methods='GET',
        handler=CursoHandler,
        handler_method='list_ents'
    ),
    Route(
        name='cursohandler.list',
        template=r'/cursos',
        methods='GET',
        handler=CursoHandler,
        handler_method='list'
    ),
    Route(
        name='cursohandler.view',
        template=r'/curso/view_criar',
        methods=None,
        handler=CursoHandler,
        handler_method='view'
    ),
    Route(
        name='cursohandler.post',
        template=r'/curso/criar',
        methods=None,
        handler=CursoHandler,
        handler_method='post'
    ),
    Route(
        name='cursohandler.view_update',
        template=r'/curso/<id:(\d+)>/view_atualizar',
        methods=None,
        handler=CursoHandler,
        handler_method='view_update'
    ),
    Route(
        name='cursohandler.put',
        template=r'/curso/<id:(\d+)>/atualizar',
        methods=None,
        handler=CursoHandler,
        handler_method='put'
    ),
    Route(
        name='cursohandler.delete',
        template=r'/curso/<id:(\d+)>/apagar',
        methods=None,
        handler=CursoHandler,
        handler_method='delete'
    ),
    ('/.*', NotFoundPageHandler),
], debug=True)
