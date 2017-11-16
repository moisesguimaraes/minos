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
    perguntas = ndb.StringProperty(indexed=False, repeated=True)
    materias = ndb.StringProperty(indexed=False, repeated=True)
    alunos = ndb.StringProperty(repeated=True)


class Materia(ndb.Model):
    user_id = ndb.IntegerProperty()
    titulo = ndb.StringProperty(indexed=False)
    professor = ndb.StringProperty(indexed=False)
    periodo = ndb.StringProperty(indexed=False)


class Aluno(ndb.Model):
    user_id = ndb.IntegerProperty()
    matricula = ndb.StringProperty(indexed=False)
    nome = ndb.StringProperty(indexed=False)
    periodo = ndb.StringProperty(indexed=False)


class Codigo(ndb.Model):
    nomeAluno = ndb.StringProperty(indexed=False)
    periodo = ndb.StringProperty(indexed=False)
    codigo = ndb.StringProperty(indexed=False)

class Contador(ndb.Model):
    id_perguntas = ndb.IntegerProperty() 
    id_formularios = ndb.IntegerProperty()
    id_materias = ndb.IntegerProperty()
    maior_cod = ndb.IntegerProperty()

class Resultado(ndb.Model):
    aluno = ndb.IntegerProperty()
    formulario = ndb.IntegerProperty()
    enunciado = ndb.StringProperty(indexed=False)
    respostas = ndb.StringProperty(indexed=False)
