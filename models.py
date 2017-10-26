# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, import-error

from google.appengine.ext import ndb


class Admin(ndb.Model):
    usuario = ndb.StringProperty(indexed=False)
    senha = ndb.StringProperty(indexed=False)


class Pergunta(ndb.Model):
    tipo = ndb.StringProperty(indexed=False)
    enunciado = ndb.TextProperty()
    resposta = ndb.PickleProperty()


class Formulario(ndb.Model):
    nome = ndb.StringProperty(indexed=False)
    perguntas = ndb.StructuredProperty(Pergunta, repeated=True)


class Disciplina(ndb.Model):
    nome = ndb.StringProperty(indexed=False)
    professor = ndb.StringProperty(indexed=False)
    formulario = ndb.StructuredProperty(Formulario)
    periodo = ndb.StringProperty(indexed=False)


class Aluno(ndb.Model):
    matricula = ndb.StringProperty(indexed=False)
    finalizado = ndb.BooleanProperty()
    codigo = ndb.StringProperty(indexed=False)
    codigo_usado = ndb.BooleanProperty()
    progresso = ndb.PickleProperty(default={})
    """disciplinas = ndb.StructuredProperty(Disciplina, repeated=True)"""
