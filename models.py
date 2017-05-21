# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, import-error

from google.appengine.ext import ndb

class Disciplina(ndb.Model):
    nome = ndb.StringProperty()
    professor = ndb.IntegerProperty()
    periodo = ndb.StringProperty()
