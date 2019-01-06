# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, import-error

from google.appengine.ext import ndb


class Pergunta(ndb.Model):
    user_id = ndb.IntegerProperty()
    avaliado = ndb.IntegerProperty()
    tipo = ndb.IntegerProperty()
    enunciado = ndb.TextProperty()
    respostas = ndb.StringProperty(repeated=True)


class Aluno(ndb.Model):
    matricula = ndb.StringProperty()
    nome = ndb.StringProperty(indexed=False)
    periodo = ndb.StringProperty(indexed=False)

    @classmethod
    def query_aluno(cls, matricula):
        als = None
        if matricula:
            als = cls.query(cls.matricula == matricula).get()
        return als


class Contador(ndb.Model):
    user_id = ndb.IntegerProperty(default=1)
    id_perguntas = ndb.IntegerProperty(default=1) 
    id_formularios = ndb.IntegerProperty(default=1)
    id_materias = ndb.IntegerProperty(default=1)
    id_turmas = ndb.IntegerProperty(default=1)
    maior_cod = ndb.IntegerProperty(default=1)
    id_cursos = ndb.IntegerProperty(default=1)


class Turma(ndb.Model):
    id_curso = ndb.IntegerProperty()
    user_id = ndb.IntegerProperty()
    periodo = ndb.StringProperty(indexed=False)
    alunos = ndb.IntegerProperty(repeated=True)
    materias = ndb.IntegerProperty(repeated=True)


class Formulario(ndb.Model):
    user_id = ndb.IntegerProperty()
    titulo = ndb.StringProperty(indexed=False)
    descricao = ndb.StringProperty(indexed=False)
    perguntas = ndb.IntegerProperty(repeated=True)
    turmas = ndb.IntegerProperty(repeated=True)

 
class Materia(ndb.Model):
    id_curso = ndb.IntegerProperty()
    user_id = ndb.IntegerProperty()
    titulo = ndb.StringProperty(indexed=False)
    professor = ndb.StringProperty(indexed=False)
    periodo = ndb.StringProperty(indexed=False)


class Admin(ndb.Model):
    usuario = ndb.StringProperty()
    senha = ndb.StringProperty()

    @classmethod
    def query_admin(cls, usuario,senha):
        als = None
        if usuario and senha:
            q = cls.query()
            for qq in q:
                if qq.usuario ==  usuario and qq.senha == senha:
                    als = qq
                    break
        return als

class Codigo(ndb.Model):
    id_aluno = ndb.IntegerProperty()
    id_formulario = ndb.IntegerProperty()
    nomeAluno = ndb.StringProperty()
    periodo = ndb.StringProperty(indexed=False)
    codigo = ndb.StringProperty()


class Resultado(ndb.Model):
    id_curso = ndb.IntegerProperty()
    id_aluno = ndb.IntegerProperty()
    id_formulario = ndb.IntegerProperty()
    id_pergunta = ndb.IntegerProperty()
    enunciado = ndb.StringProperty(indexed=False)
    respostas = ndb.StringProperty(repeated=True,indexed=False)
    matricula_aluno  = ndb.StringProperty(indexed=False)
    titulo_formulario = ndb.StringProperty(indexed=False)
    periodo = ndb.StringProperty(indexed=False)
    avaliado = ndb.StringProperty(indexed=False)
    nome_curso = ndb.StringProperty(indexed=False)


class Progresso(ndb.Model):
    user_id = ndb.IntegerProperty()
    matricula = ndb.StringProperty()
    formulario = ndb.IntegerProperty()
    progresso = ndb.IntegerProperty(default=0)


class Curso(ndb.Model):
    cod = ndb.IntegerProperty()
    nome = ndb.StringProperty()
    descricao = ndb.StringProperty()