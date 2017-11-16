#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import jinja2
import time
import webapp2

from datetime import datetime
from hashlib import sha224
from os.path import dirname, join
from google.appengine.ext import ndb
from models import *

template_dir = join(dirname(__file__), "templates")
data_dir = join(dirname(__file__), "data")
gestao_comercial_data = json.loads(open(join(
    data_dir, "gestao_comercial.json")).read())

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir), autoescape=True)
gestao_comercial_html = jinja_env.get_template(
    "gestao_comercial.html").render(curso=gestao_comercial_data)


DATA_COOKIE = dict()


def gerador_cookie():
    dtime = datetime.now()
    return sha224(dtime.isoformat()).hexdigest()


class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, *template, **kw):
        t = jinja_env.get_template(*template)
        return t.render(**kw)

    def render(self, *template, **kw):
        self.write(self.render_str(*template, **kw))

class MainHandler(Handler):

    def get(self):
        self.write(gestao_comercial_html)


class AlunoHandler(Handler):

    def get(self):
        self.render("loginAluno.html")

    def post(self):
        matricula = self.request.get('mat')
        aluno = ndb.Key(Aluno, matricula).get()
        if aluno != None and matricula == aluno.matricula:
            self.redirect('/formularios' + '?mat='+ matricula+'')
        else:
            self.redirect('/aluno')


class LoginHandler(Handler):

    def get(self):
        self.render("loginAdmin.html")

    def post(self):
        usuario = self.request.get('usuario')
        senha = self.request.get('senha')
        if usuario == "a" and senha == "a":
            self.redirect('/admin')
        else:
            self.redirect('/login')


class FormulariosHandler(Handler):

    def get(self):
        matricula = self.request.get('mat')
        forms = Formulario.query(Formulario.alunos.IN([matricula]))
        form = []
        for formu in forms:
            d = {
                "titulo": formu.titulo,
                "descricao": formu.descricao,
                "codigo": formu.user_id,
                "progresso": 0}
            form.append(d)
        self.render("formularios.html", formularios=form)


class AvaliacaoHandler(Handler):
    def get(self):
        form = int(self.request.get("form"))
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
        
        # else:
        #     self.redirect("/avaliar?form=%d" % (int(form)))


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
        self.render("Administrador.html")


class ListarFormularios(Handler):
    def get(self):
        formularios = Formulario.query()
        page = {
            "titulo": u"Formulários",
            "formularios": formularios
        }
        self.render("Administrador.html", page=page)


class ListarAlunos(Handler):
    def get(self):
        alunos = Aluno.query()
        page = {
            "titulo": "Alunos",
            "alunos": alunos
        }
        self.render("Administrador.html", page=page)


class ListarMaterias(Handler):
    def get(self):
        materias = Materia.query()
        page = {
            "titulo": u"Matérias",
            "materias": materias
        }
        self.render("Administrador.html", page=page)


class ListarPerguntas(Handler):
    def get(self):
        perguntas = Pergunta.query()
        page = {
            "titulo": "Perguntas",
            "perguntas": perguntas
        }
        self.render("Administrador.html", page=page)


class CriarFormulario(Handler):
    def get(self):
        alunos = Aluno.query()
        materias = Materia.query()
        perguntas = Pergunta.query()
        page = {
            "alunos": alunos,
            "materias": materias,
            "perguntas": perguntas
        }
        self.render("criarformulario.html", page=page)

    def post(self):
        titulo = self.request.get('titulo')
        descricao = self.request.get('descricao')
        aluno = self.request.get_all('aluno')
        mat = self.request.get_all('mat')
        perg = self.request.get_all('perg')
        cont = ndb.Key(Contador, 1).get()
        if not cont:
            cont = Contador(id_formularios=1, id_perguntas=1, id_materias=1, id=1)
        form = Formulario(titulo=titulo, descricao=descricao, perguntas=perg, materias=mat, alunos=aluno, id=cont.id_formularios, user_id=cont.id_formularios)
        cont.id_formularios += 1
        cont.put()
        form.put()
        time.sleep(.1)
        self.redirect('/listarformularios')


class CriarAluno(Handler):
    def get(self):
        page = {"titulo": "Aluno", "tipo": 1}
        self.render("editar.html", page=page)

    def post(self):
        matricula = self.request.get('matricula')
        periodo = self.request.get('periodo')
        nome = self.request.get('nome')
        aluno = Aluno(matricula=matricula, periodo=periodo, nome=nome, id=int(matricula), user_id=int(matricula))
        aluno.put()
        time.sleep(.1)
        self.redirect("/listaralunos")


class CriarMateria(Handler):
    def get(self):
        page = {"titulo": "Materia", "tipo": 1}
        self.render("editar.html", page=page)

    def post(self):
        titulo = self.request.get('titulo')
        professor = self.request.get('professor')
        periodo = self.request.get('periodo')
        cont = ndb.Key(Contador, 1).get()
        if not cont:
            cont = Contador(id_formularios=1, id_perguntas=1, id_materias=1, id=1)
        materia = Materia(titulo=titulo, professor=professor, periodo=periodo, id=cont.id_materias, user_id=cont.id_materias)
        cont.id_materias += 1
        cont.put()
        materia.put()
        time.sleep(.1)
        self.redirect("/listarmaterias")


class CriarPergunta(Handler):
    def get(self):
        self.render("criarpergunta.html")

    def post(self):
        # cookie = self.request.get('Cookie')
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


class ApagarFormulario(Handler):
    def get(self):
        id = int(self.request.get('id'))
        form = ndb.Key(Formulario, id).get()
        form.key.delete()
        time.sleep(.1)
        self.redirect('/listarformularios')


class ApagarPergunta(Handler):
    def get(self):
        id = int(self.request.get('id'))
        perg = ndb.Key(Pergunta, id).get()
        perg.key.delete()
        time.sleep(.1)
        self.redirect('/listarperguntas')


class ApagarMateria(Handler):
    def get(self):
        id = int(self.request.get('id'))
        mat = ndb.Key(Materia, id).get()
        mat.key.delete()
        time.sleep(.1)
        self.redirect('/listarmaterias')


class ApagarAluno(Handler):
    def get(self):
        id = int(self.request.get('id'))
        aluno = ndb.Key(Aluno, id).get()
        aluno.key.delete()
        time.sleep(.1)
        self.redirect('/listaralunos')


class EditarFormulario(Handler):
    def get(self):
        id = int(self.request.get('id'))
        form = ndb.Key(Formulario, id).get()
        al = list(map(int, form.alunos))
        mat = list(map(int, form.materias))
        perg = list(map(int, form.perguntas))
        alunos = Aluno.query(Aluno.user_id.IN(al))
        materias = Materia.query(Materia.user_id.IN(mat))
        perguntas = Pergunta.query(Pergunta.user_id.IN(perg))
        page = {
            "formulario": form,
            "alunos": alunos,
            "materias": materias,
            "perguntas": perguntas
        }
        self.render("editarformulario.html", page=page)
    
    def post(self):
        id = int(self.request.get('id'))
        titulo = self.request.get('titulo')
        descricao = self.request.get('descricao')
        aluno = self.request.get_all('aluno')
        mat = self.request.get_all('mat')
        perg = self.request.get_all('perg')
        form = ndb.Key(Formulario, id).get()
        form.titulo = titulo
        form.descricao = descricao
        form.perguntas = perg
        form.materias = mat
        form.alunos = aluno
        form.put()
        time.sleep(.1)
        self.redirect('/listarformularios')


class EditarAluno(Handler):
    def get(self):
        id = int(self.request.get('id'))
        aluno = ndb.Key(Aluno, id).get()
        page = {"titulo": "Aluno", "tipo": 2, "objeto": aluno}
        self.render("editar.html", page=page)

    def post(self):
        id = int(self.request.get('id'))
        matricula = self.request.get('matricula')
        periodo = self.request.get('periodo')
        nome = self.request.get('nome')
        aluno = ndb.Key(Aluno, id).get()
        aluno.key.delete()
        aluno = Aluno(matricula=matricula, periodo=periodo, nome=nome, id=int(matricula), user_id=int(matricula))
        # aluno.matricula = matricula
        # aluno.periodo = periodo
        # aluno.nome = nome
        aluno.put()
        time.sleep(.1)
        self.redirect('/listaralunos')


class EditarMateria(Handler):
    def get(self):
        id = int(self.request.get('id'))
        mat = ndb.Key(Materia, id).get()
        page = {"titulo": "Materia", "tipo": 2, "objeto": mat}
        self.render("editar.html", page=page)

    def post(self):
        id = int(self.request.get('id'))
        titulo = self.request.get('titulo')
        professor = self.request.get('professor')
        periodo = self.request.get('periodo')
        mat = ndb.Key(Materia, id).get()
        mat.titulo = titulo
        mat.professor = professor
        mat.periodo = periodo
        mat.put()
        time.sleep(.1)
        self.redirect('/listarmaterias')


class EditarPergunta(Handler):
    def get(self):
        id = int(self.request.get('id'))
        perg = ndb.Key(Pergunta, id).get()
        self.render("editarpergunta.html", pergunta=perg)
    
    def post(self):
        id = int(self.request.get('id'))
        perg = ndb.Key(Pergunta, id).get()
        enunciado = self.request.get('enunciado')
        tipo = int(self.request.get('tipo'))
        respostas = self.request.get_all('resposta')
        perg.tipo = tipo
        perg.enunciado = enunciado
        perg.respostas = respostas
        perg.put()
        time.sleep(.1)
        self.redirect('/listarperguntas')


# class Teste(Handler):
#     def get(self):
#         aluno = ndb.Key(Aluno, 1).get()
        
#         self.write(aluno == None)


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
    # ('/teste', Teste)
], debug=True)
