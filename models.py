# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, import-error

from google.appengine.ext import ndb


class Admin(ndb.Model):
    usuario = ndb.StringProperty(indexed=False)
    senha = ndb.StringProperty(indexed=False)


class Pergunta(ndb.Model):
    user_id = ndb.IntegerProperty()
    tipo = ndb.IntegerProperty()
    enunciado = ndb.TextProperty()
    respostas = ndb.StringProperty(repeated=True)


class Formulario(ndb.Model):
    user_id = ndb.IntegerProperty()
    titulo = ndb.StringProperty(indexed=False)
    descricao = ndb.StringProperty(indexed=False)
    perguntas = ndb.IntegerProperty(repeated=True)


class Materia(ndb.Model):
    user_id = ndb.IntegerProperty()
    titulo = ndb.StringProperty(indexed=False)
    professor = ndb.StringProperty(indexed=False)
    periodo = ndb.StringProperty(indexed=False)
    formularios = ndb.IntegerProperty(repeated=True)


class Aluno(ndb.Model):
    user_id = ndb.IntegerProperty()
    matricula = ndb.StringProperty(indexed=False)
    nome = ndb.StringProperty(indexed=False)
    periodo = ndb.StringProperty(indexed=False)
    materias = ndb.IntegerProperty(repeated=True)


class Codigo(ndb.Model):
    nomeAluno = ndb.StringProperty()
    periodo = ndb.StringProperty(indexed=False)
    codigo = ndb.StringProperty()
    formulario = ndb.IntegerProperty()

class Contador(ndb.Model):
    id_perguntas = ndb.IntegerProperty() 
    id_formularios = ndb.IntegerProperty()
    id_materias = ndb.IntegerProperty()
    maior_cod = ndb.IntegerProperty()

class Resultado(ndb.Model):
    materia = ndb.StringProperty(indexed=False)
    enunciado = ndb.StringProperty(indexed=False)
    respostas = ndb.StringProperty(repeated=True)

class Progresso(ndb.Model):
    matricula = ndb.IntegerProperty()
    formulario = ndb.IntegerProperty()
    progresso = ndb.IntegerProperty()