# -*- coding: utf-8 -*-

import json
import time
import urllib
from os.path import dirname, join

from jinja2 import Environment, FileSystemLoader
from webapp2 import RequestHandler, Route, WSGIApplication, cached_property
from webapp2_extras import sessions

from google.appengine.ext import ndb
from models import *

TEMPLATE_DIR = join(dirname(__file__), "templates")
# DATA_DIR = join(dirname(__file__), "data")
# GESTAO_COMERCIAL_DATA = json.loads(open(join(
#     DATA_DIR, "gestao_comercial.json")).read())

JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
# GESTAO_COMERCIAL_HTML = JINJA_ENV.get_template(
#     "index.html").render(curso=GESTAO_COMERCIAL_DATA)


DATA_COOKIE = dict()

class Handler(RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, *template, **kw):
        tmp = JINJA_ENV.get_template(*template)
        return tmp.render(**kw)

    def render(self, *template, **kw):
        self.write(self.render_str(*template, **kw))

    def json_encode(self, objs):
        self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
        query_dict = [
            dict(obj.to_dict(),
            **dict(id=obj.key.id()))
            for obj in objs]
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
    
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


######################## Aluno ########################
class LoginAlunoHandler(Handler):

    def get(self):
        self.render("Aluno/loginaluno.html")

    def post(self):
        matricula = self.request.get('mat', '')
        aluno = Aluno.query_aluno(matricula)
        if aluno:
            self.session['aluno'] = aluno.key.id()
            self.redirect('/alunos/formularios')
        else:
            self.redirect('/')


class AvaliacaoHandler(Handler):
    
    def get(self):
        id_aluno = self.session.get('aluno', '')
        if id_aluno:
            turma = Turma.query(
                Turma.alunos.IN(
                    [int(id_aluno)]
                )
            ).get()
            page = []
            if turma:
                progs = Progresso.query(
                    Progresso.user_id == int(id_aluno)
                )
                formularios = Formulario.query(
                    Formulario.turmas.IN(
                        [turma.key.id()]
                    )
                )
                for form in formularios:
                    prog = progs.filter(
                            Progresso.formulario == form.key.id()
                    ).get()
                    if prog:
                        prog = int((float(prog.progresso)/len(form.perguntas))*100.0)
                    else:
                        prog = 0
                    page.append((form, prog))
            self.render('Aluno/formularios.html', page=page)
        else:
            self.redirect('/')


class HandlerForm(Handler):
    
    def get(self, formulario):
        id_aluno = self.session.get('aluno', '')
        if id_aluno and formulario.isdigit():
            form = ndb.Key(Formulario, int(formulario)).get()
            if form:
                prog = Progresso.query(ndb.AND(
                    Progresso.user_id == int(id_aluno),
                    Progresso.formulario == form.key.id()
                )).get()
                pergunta = None
                if (prog) and (prog.progresso >= len(form.perguntas)):
                    self.redirect("/alunos/formularios")
                else:
                    pergunta = form.perguntas[ 0 if not prog else prog.progresso ]
                self.redirect('/alunos/pergunta/%d/%d' % (int(formulario), int(pergunta)))
            else:
                self.redirect('/')
        else:
            self.redirect('/')


class AvaliacaoPerguntaHandler(Handler):
    
    def get(self, formulario, id):
        id_aluno = self.session.get('aluno', '')
        if id_aluno and formulario.isdigit() and id.isdigit():
            turma = Turma.query(
                Turma.alunos.IN(
                    [int(id_aluno)]
                )
            ).get()
            form = ndb.Key(Formulario, int(formulario)).get()
            pergunta = ndb.Key(Pergunta, int(id)).get()
            materias = []
            if pergunta.avaliado == 1:
                materias = ndb.get_multi(
                    [ndb.Key(Materia, int(k)) for k in turma.materias]
                )
            page = {
                "pergunta": pergunta,
                "materias": materias,
                "formulario": form
            }
            self.render('Aluno/questao.html', page=page)
        else:
            self.redirect('/')
    
    def post(self, formulario, id):
        id_aluno = self.session.get('aluno', '')
        if id_aluno and formulario.isdigit() and id.isdigit():
            user = ndb.Key(Aluno, int(id_aluno)).get()
            turma = Turma.query(
                Turma.alunos.IN(
                    [int(id_aluno)]
                )
            ).get()
            formular = ndb.Key(Formulario, int(formulario)).get()
            pergunta = ndb.Key(Pergunta, int(id)).get()
            curso = ndb.Key(Curso, int(turma.id_curso)).get()
            res = []
            if pergunta.avaliado == 1:
                materias = ndb.get_multi(
                    [ndb.Key(Materia, int(k)) for k in turma.materias]
                )
                if materias:
                    for materia in materias:
                        res.append(
                            Resultado(
                                id_curso=turma.id_curso,
                                id_aluno=user.key.id(),
                                matricula_aluno=user.matricula,
                                id_formulario=formular.key.id(),
                                id_pergunta=pergunta.key.id(),
                                titulo_formulario=formular.titulo,
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
                        id_formulario=formular.key.id(),
                        id_pergunta=pergunta.key.id(),
                        titulo_formulario=formular.titulo,
                        enunciado=pergunta.enunciado,
                        respostas=self.request.get_all('outros'),
                        periodo=user.periodo,
                        avaliado='outros',
                        nome_curso=curso.nome
                    )
                )
            prog = Progresso.query(ndb.AND(
                    Progresso.user_id == user.key.id(),
                    Progresso.formulario == formular.key.id()
                )).get()
            if prog:
                prog.progresso += 1
            else:
                prog = Progresso(
                    user_id=user.key.id(),
                    matricula=user.matricula,
                    formulario=formular.key.id(),
                    progresso=1
                )
            ndb.put_multi(res)
            prog.put()
            time.sleep(.1)
            if len(formular.perguntas) > prog.progresso:
                self.redirect('/alunos/pergunta/%d/%d' % (
                    int(formulario),
                    int(formular.perguntas[prog.progresso])
                    ))
            else:
                self.redirect('/alunos/points/%d' % (int(formulario)))
        else:
            self.redirect('/')


class CodigoHandler(Handler):

    def get(self, formulario):
        id_aluno = self.session.get('aluno', '')
        if id_aluno and formulario.isdigit():
            aluno = ndb.Key(Aluno, int(id_aluno)).get()
            form = ndb.Key(Formulario, int(formulario)).get()
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


######################## Professor ########################
class ProfessorHandler(Handler):
    
    def get(self):
        self.render("Prof/professor.html")
    
    def post(self): 
        codigo = self.request.get('codigo', '')
        if codigo:
            codigos = Codigo.query(
                Codigo.codigo == codigo
            ).fetch(keys_only=True)
            if codigos:
                cod = codigos.pop(0).get()
                self.session['professor'] = cod.key.id()
                self.redirect('/validar')
            else:
                self.redirect('/professor')
        else:
            self.redirect('/professor')


class ValidarCodigo(Handler):

    def get(self):
        cod_prof = self.session.get('professor', '')
        if cod_prof:
            codigo = ndb.Key(Codigo, int(cod_prof)).get()
            self.render("Prof/validar.html", codigo=codigo)
        else:
            self.redirect('/professor')

    def post(self):
        cod_prof = self.session.get('professor', '')
        if cod_prof:
            codigo = ndb.Key(Codigo, int(cod_prof)).get()
            codigo.key.delete()
            time.sleep(.1)
            self.session.pop("professor")
            self.redirect('/professor')
        else:
            self.redirect('/professor')


######################## Adminitrador ########################
class LoginHandler(Handler):
    
    def get(self):
        self.render("Admin/loginadmin.html")

    def post(self):
        usuario = self.request.get('usuario','')
        senha = self.request.get('senha','')
        admin = Admin.query_admin(usuario,senha)
        if admin:
            self.session['admin'] = admin.key.id()
            self.redirect('/admin')
        else:
            self.redirect('/login')


class AdministradorHandler(Handler):

    def get(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/administrador.html")
        else:
            self.redirect('/login')


class FormularioHandler(Handler):
    def list_ents(self):
        id_admin = self.session.get('admin','')
        if id_admin:
            self.render("Admin/listar_formularios.html")
        else:
            self.redirect('/login')

            
    
    def list(self):
        id_admin = self.session.get('admin','')
        if id_admin:
            self.json_encode(Formulario.query())
        else:
            self.redirect('/login')

    
    def view(self):
        id_admin = self.session.get('admin','')
        if id_admin:
            self.render("Admin/criarformulario.html")
        else:
            self.redirect('/login')

    
    def post(self):
        id_admin = self.session.get('admin','')
        if id_admin:
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

    
    def view_update(self, id):
        id_admin = self.session.get('admin','')
        if id_admin:
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

    
    def put(self, id):
        id_admin = self.session.get('admin','')
        if id_admin:
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


    def delete(self, id):
        id_admin = self.session.get('admin','')
        if id_admin:
            ndb.Key(Formulario, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/formularios')
        else:
            self.redirect('/login')


class PerguntaHandler(Handler):
    def list_ents(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_perguntas.html")
        else:
            self.redirect('/login')

    
    def list(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Pergunta.query())
        else:
            self.redirect('/login')

    
    def view(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criarpergunta.html")
        else:
            self.redirect('/login')

    
    def post(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
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

    
    def view_update(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            perg = ndb.Key(Pergunta, int(id)).get()
            page = {
                "pergunta": perg
            }
            self.render("Admin/editarpergunta.html", page=page)
        else:
            self.redirect('/login')

    
    def put(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
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


    def delete(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Pergunta, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/perguntas')
        else:
            self.redirect('/login')


class MateriaHandler(Handler):
    def list_ents(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_materias.html")
        else:
            self.redirect('/login')

    
    def list(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Materia.query())
        else:
            self.redirect('/login')

    
    def view(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criarmateria.html")
        else:
            self.redirect('/login')

    
    def post(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
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

    
    def view_update(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            mat = ndb.Key(Materia, int(id)).get()
            page = {
                "materia": mat
            }
            self.render("Admin/editarmateria.html", page=page)
        else:
            self.redirect('/login')

    
    def put(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
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


    def delete(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Materia, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/materias')
        else:
            self.redirect('/login')


class AlunoHandler(Handler):
    def list_ents(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_alunos.html")
        else:
            self.redirect('/login')

    
    def list(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Aluno.query())
        else:
            self.redirect('/login')

    
    def view(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criaraluno.html")
        else:
            self.redirect('/login')

    
    def post(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
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

    
    def view_update(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            aluno = ndb.Key(Aluno, int(id)).get()
            page = {
                "aluno": aluno
            }
            self.render("Admin/editaraluno.html", page=page)
        else:
            self.redirect('/login')

    
    def put(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
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


    def delete(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Aluno, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/alunos')
        else:
            self.redirect('/login')


class TurmaHandler(Handler):
    def list_ents(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_turmas.html")
        else:
            self.redirect('/login')

    
    def list(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Turma.query())
        else:
            self.redirect('/login')

    
    def view(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criarturma.html")
        else:
            self.redirect('/login')

    
    def post(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
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

    
    def view_update(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
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

    
    def put(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
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


    def delete(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Turma, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/turmas')
        else:
            self.redirect('/login')


class RelatorioHandler(Handler):

    def list_ents(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            forms = Formulario.query()
            page ={
                "formularios": forms
            }
            self.render("Admin/listar_relatorio.html",page=page)
        else:
            self.redirect('/login')

    
    def list(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
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


class CursoHandler(Handler):
    def list_ents(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_cursos.html")
        else:
            self.redirect('/login')

    def list(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Curso.query())
        else:
            self.redirect('/login')
    
    def view(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criarcurso.html")
        else:
            self.redirect('/login')
    
    def post(self):
        id_admin = self.session.get('admin', '')
        if id_admin:
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
    
    def view_update(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            curso = ndb.Key(Curso, int(id)).get()
            page = {
                "curso": curso
            }
            self.render("Admin/editarcurso.html", page=page)
        else:
            self.redirect('/login')

    def put(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
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

    def delete(self, id):
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Curso, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/cursos')
        else:
            self.redirect('/login')


class LogoutHandler(Handler):
    
    def get(self):
        if self.session:
            if self.session.get('admin',''):
                self.session.pop('admin')
            elif self.session.get('aluno',''):
                self.session.pop('aluno')
        self.redirect('/')


class NotFoundPageHandler(Handler):
    def get(self):
        self.redirect('/')


app = WSGIApplication([
    ('/logout', LogoutHandler),
    ('/', LoginAlunoHandler),
    ('/login', LoginHandler),
    ('/professor', ProfessorHandler),
    ('/alunos/formularios', AvaliacaoHandler),
    ('/validar', ValidarCodigo),
    ('/admin', AdministradorHandler),
    Route(
        name='points.get',
        template=r'/alunos/points/<formulario:(\d+)>',
        methods='GET',
        handler=CodigoHandler,
        handler_method='get'
    ),
    Route(
        name='avalicsdafaohandler.get',
        template=r'/alunos/formularios/<formulario:(\d+)>',
        methods='GET',
        handler=HandlerForm,
        handler_method='get'
    ),
    Route(
        name='avalicaohandler.get',
        template=r'/alunos/pergunta/<formulario:(\d+)>/<id:(\d+)>',
        methods='GET',
        handler=AvaliacaoPerguntaHandler,
        handler_method='get'
    ),
    Route(
        name='avalicaohandler.post',
        template=r'/alunos/pergunta/<formulario:(\d+)>/<id:(\d+)>',
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
], config={'webapp2_extras.sessions': {'secret_key': 'my-super-secret-key',}}, debug=True)
