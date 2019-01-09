# -*- coding: utf-8 -*-

# imports do python
import json
import time
import urllib
from os.path import dirname, join

#imports do jinja2
from jinja2 import Environment, FileSystemLoader

# imports do appengine
from webapp2 import RequestHandler, Route, WSGIApplication, cached_property
from webapp2_extras import sessions

from google.appengine.ext import ndb
from models import *

# Carregando o Jinja2
TEMPLATE_DIR = join(dirname(__file__), "templates")
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)


class Handler(RequestHandler):
    """
    Classe auxiliar para manipulação requisições
    """

    def write(self, *a, **kw):
        """Retorna a mensagem ou template renderizado"""
        self.response.out.write(*a, **kw)

    def render_str(self, *template, **kw):
        """Pega o template e retorna renderizado"""
        tmp = JINJA_ENV.get_template(*template)
        return tmp.render(**kw)

    def render(self, *template, **kw):
        """Chama o metodo write e passa os parametros pra renderizar o template"""
        self.write(self.render_str(*template, **kw))

    def json_encode(self, objs):
        """Retorna um a lista de entidades em json"""
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
    """
    Classe responsavel pelo login dos alunos
    """

    def get(self):
        """Renderiza o template de login dos alunos"""
        self.render("Aluno/loginaluno.html")

    def post(self):
        """Confere se a matricula existe e seta a session para a requisição"""
        matricula = self.request.get('mat', '')
        aluno = Aluno.query_aluno(matricula) # Procura o aluno no banco de dados pela matricula
        if aluno:
            self.session['aluno'] = aluno.key.id() # Seta a session
            self.redirect('/alunos/formularios')
        else:
            self.redirect('/')
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='loginaluno.get',
                template=r'/',
                methods='GET',
                handler=LoginAlunoHandler,
                handler_method='get'
            ),
            Route(
                name='loginaluno.post',
                template=r'/',
                methods='POST',
                handler=LoginAlunoHandler,
                handler_method='post'
            ),
        ]


class AvaliacaoHandler(Handler):
    """
    Classe responsavel por Listar os Formularios de cada aluno
    """
    
    def get(self):
        """Renderiza o template com os formularios dos alunos"""
        id_aluno = self.session.get('aluno', '')
        if id_aluno:
            turma = Turma.query( # Busca a turma do aluno 
                Turma.alunos.IN(
                    [int(id_aluno)]
                )
            ).get()
            page = []
            if turma:
                progs = Progresso.query( # Lista os progressos do aluno
                    Progresso.user_id == int(id_aluno)
                )
                formularios = Formulario.query( # Lista os formularios da turma do aluno
                    Formulario.turmas.IN(
                        [turma.key.id()]
                    )
                )
                for form in formularios: # Percorre a lista de formluarios
                    prog = progs.filter(
                        # Busca o progresso do aluno por formulario
                        Progresso.formulario == form.key.id() 
                    ).get()
                    if prog and not (prog.progresso >= len(form.perguntas)):
                        # Pega o id da proxima pergunta
                        pergunta = form.perguntas[prog.progresso]
                        # Calcula o progresso no formulario
                        prog = int((float(prog.progresso)/len(form.perguntas))*100.0)
                    elif prog:
                        pergunta = -1
                        prog = int((float(prog.progresso)/len(form.perguntas))*100.0)
                    else:
                        pergunta = form.perguntas[0]
                        prog = 0
                    page.append((form, prog, pergunta))
            self.render('Aluno/formularios.html', page=page)
        else:
            self.redirect('/')
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='avaliacaohandler.get',
                template=r'/alunos/formularios',
                methods='GET',
                handler=AvaliacaoHandler,
                handler_method='get'
            ),
            Route(
                name='avaliacaohandler.post',
                template=r'/alunos/formularios',
                methods='POST',
                handler=AvaliacaoHandler,
                handler_method='post'
            ),
        ]


class AvaliacaoPerguntaHandler(Handler):
    """
    Classe responsavel pelas perguntas dos formularios para os alunos
    """
    
    def get(self, formulario, id):
        """Renderiza a pergunta para o aluno"""
        id_aluno = self.session.get('aluno', '')
        if id_aluno and formulario.isdigit() and id.isdigit():
            turma = Turma.query(
                Turma.alunos.IN( # Busca a turma do aluno
                    [int(id_aluno)]
                )
            ).get()
            form = ndb.Key(Formulario, int(formulario)).get() #Pega o formulario
            pergunta = ndb.Key(Pergunta, int(id)).get() # Pega a pergunta
            materias = []
            if pergunta.avaliado == 1:
                materias = ndb.get_multi( # Lista as materias
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
        """Salva as respostas da pergunta no banco de dados"""
        id_aluno = self.session.get('aluno', '')
        if id_aluno and formulario.isdigit() and id.isdigit():
            user = ndb.Key(Aluno, int(id_aluno)).get()
            turma = Turma.query(
                Turma.alunos.IN(  # Busca a turma do aluno
                    [int(id_aluno)]
                )
            ).get()
            formular = ndb.Key(Formulario, int(formulario)).get() #Pega o formulario
            pergunta = ndb.Key(Pergunta, int(id)).get() # Pega a pergunta
            curso = ndb.Key(Curso, int(turma.id_curso)).get() # Pega o curso
            res = []
            if pergunta.avaliado == 1:
                materias = ndb.get_multi( # Lista as materias
                    [ndb.Key(Materia, int(k)) for k in turma.materias]
                )
                if materias:
                    for materia in materias:
                        res.append(
                            Resultado( # Criar os resultados por materia
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
                    Resultado( # Criar os resultados por outros
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
            prog = Progresso.query(ndb.AND( # Pega o progresso 
                    Progresso.user_id == user.key.id(),
                    Progresso.formulario == formular.key.id()
                )).get()
            if prog:
                prog.progresso += 1
            else:
                prog = Progresso( # Cria o progresso caso ele não exista 
                    user_id=user.key.id(),
                    matricula=user.matricula,
                    formulario=formular.key.id(),
                    progresso=1
                )
            ndb.put_multi(res) # Adiciona todas as respostas ao Banco
            prog.put() # Adiciona o progresso ao Banco
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
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='avalicaoperguntahandler.get',
                template=r'/alunos/pergunta/<formulario:(\d+)>/<id:(\d+)>',
                methods='GET',
                handler=AvaliacaoPerguntaHandler,
                handler_method='get'
            ),
            Route(
                name='avalicaoperguntahandler.post',
                template=r'/alunos/pergunta/<formulario:(\d+)>/<id:(\d+)>',
                methods='POST',
                handler=AvaliacaoPerguntaHandler,
                handler_method='post'
            ),
        ]


class CodigoHandler(Handler):
    """
    Classe responsavel por gerar o codigo de recompensa do aluno
    """

    def get(self, formulario):
        """Renderiza o codigo para o aluno"""
        id_aluno = self.session.get('aluno', '')
        if id_aluno and formulario.isdigit():
            aluno = ndb.Key(Aluno, int(id_aluno)).get() # Pega o aluno
            form = ndb.Key(Formulario, int(formulario)).get() # Pega o formulario
            progresso = Progresso.query( # Pega o progresso
                ndb.AND(
                    Progresso.formulario == form.key.id(),
                    Progresso.user_id == aluno.key.id()
                )
            ).fetch(keys_only=True)
            progresso = progresso.pop(0).get()
            if progresso.progresso == len(form.perguntas):
                cont = Contador.query(Contador.user_id == 1).get() # Pega o contador
                cod = Codigo( # Cria o codigo do aluno
                    id_aluno=aluno.key.id(),
                    nomeAluno=aluno.nome,
                    periodo=aluno.periodo,
                    id_formulario=form.key.id(),
                    codigo=str("COD" + str(cont.maior_cod))
                )
                cont.maior_cod += 1 # incrementa o contador de codigos
                codigo = cod.codigo[:]
                cod.put() # Salva o codigo
                cont.put() # Salva o contador
                time.sleep(.1)
                self.render("Aluno/gratificacao.html", codigo=codigo)
            else:
                self.redirect('/alunos/formularios')
        else:
            self.redirect('/')
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='points.get',
                template=r'/alunos/points/<formulario:(\d+)>',
                methods='GET',
                handler=CodigoHandler,
                handler_method='get'
            ),
        ]


######################## Professor ########################
class ProfessorHandler(Handler):
    """
    Classe responsavel por pegar o codigo do aluno
    """
    
    def get(self):
        """Renderiza o template de professor"""
        self.render("Prof/professor.html")
    
    def post(self):
        """Confere se o codigo existe"""
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
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='professor.get',
                template=r'/professor',
                methods='GET',
                handler=ProfessorHandler,
                handler_method='get'
            ),
            Route(
                name='professor.post',
                template=r'/professor',
                methods='POST',
                handler=ProfessorHandler,
                handler_method='post'
            ),
        ]


class ValidarCodigo(Handler):
    """
    Classe responsavel por validar e deletar o cidogo do aluno
    """

    def get(self):
        """Renderiza as informações do aluno beneficiado pelo codigo"""
        cod_prof = self.session.get('professor', '')
        if cod_prof:
            codigo = ndb.Key(Codigo, int(cod_prof)).get() # Pega o codigo do banco
            self.render("Prof/validar.html", codigo=codigo)
        else:
            self.redirect('/professor')

    def post(self):
        """Apaga o codigo do aluno"""
        cod_prof = self.session.get('professor', '')
        if cod_prof:
            codigo = ndb.Key(Codigo, int(cod_prof)).get() # Pega o codigo do banco
            codigo.key.delete() # Apaga a chave 
            time.sleep(.1)
            self.session.pop("professor")
            self.redirect('/professor')
        else:
            self.redirect('/professor')
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='validarcodigo.get',
                template=r'/validar',
                methods='GET',
                handler=ValidarCodigo,
                handler_method='get'
            ),
            Route(
                name='validarcodigo.post',
                template=r'/validar',
                methods='POST',
                handler=ValidarCodigo,
                handler_method='post'
            ),
        ]


######################## Adminitrador ########################
class LoginHandler(Handler):
    """
    Classe responsavel pelo login do Administrador
    """
    
    def get(self):
        """Renderiza o login do administrador"""
        self.render("Admin/loginadmin.html")

    def post(self):
        """Valida o usuario e senha"""
        usuario = self.request.get('usuario','')
        senha = self.request.get('senha','')
        admin = Admin.query_admin(usuario,senha) # Busca no banco pelo admin
        if admin:
            self.session['admin'] = admin.key.id()
            self.redirect('/admin/cursos')
        else:
            self.redirect('/login')
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='loginadmin.get',
                template=r'/login',
                methods='GET',
                handler=LoginHandler,
                handler_method='get'
            ),
            Route(
                name='loginadmin.post',
                template=r'/login',
                methods='POST',
                handler=LoginHandler,
                handler_method='post'
            ),
        ]


class FormularioHandler(Handler):
    """
    Classe responsável pelos Formularios
    """

    def list_ents(self):
        """Renderiza a lista de Formularios"""
        id_admin = self.session.get('admin','')
        if id_admin:
            self.render("Admin/listar_formularios.html")
        else:
            self.redirect('/login')

    def list(self):
        """Lista os formularios e responde com um json"""
        id_admin = self.session.get('admin','')
        if id_admin:
            # Lista todos os formularios e retorna como json
            self.json_encode(Formulario.query())
        else:
            self.redirect('/login')

    def view(self):
        """Renderiza a View  para criar um Formulario"""
        id_admin = self.session.get('admin','')
        if id_admin:
            self.render("Admin/criarformulario.html")
        else:
            self.redirect('/login')

    def post(self):
        """Cria o formlario e salva no banco"""
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
            form = Formulario( # Cria o formulario
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
        """Renderiza a View para atualizar o formulario"""
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
        """Salva as atualizações do formulario"""
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
        """Deleta o formulario"""
        id_admin = self.session.get('admin','')
        if id_admin:
            ndb.Key(Formulario, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/formularios')
        else:
            self.redirect('/login')

    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
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
        ]


class PerguntaHandler(Handler):
    """
    Classe responsável pelas Perguntas
    """

    def list_ents(self):
        """Renderiza a lista de Perguntas"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_perguntas.html")
        else:
            self.redirect('/login')

    def list(self):
        """Lista as Perguntas e responde com um json"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Pergunta.query())
        else:
            self.redirect('/login')

    def view(self):
        """Renderiza a View  para criar uma Pergunta"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criarpergunta.html")
        else:
            self.redirect('/login')

    def post(self):
        """Cria a pergunta e salva no banco"""
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
        """Renderiza a View para atualizar a pergunta"""
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
        """Salva as atualizações da pergunta"""
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
        """Deleta a pergunta"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Pergunta, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/perguntas')
        else:
            self.redirect('/login')
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
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
        ]


class MateriaHandler(Handler):
    """
    Classe responsável pelas Materias
    """

    def list_ents(self):
        """Renderiza a lista de Materias"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_materias.html")
        else:
            self.redirect('/login')

    def list(self):
        """Lista as Materias e responde com um json"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Materia.query())
        else:
            self.redirect('/login')

    def view(self):
        """Renderiza a View  para criar uma Materia"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criarmateria.html")
        else:
            self.redirect('/login')

    def post(self):
        """Cria a materia e salva no banco"""
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
        """Renderiza a View para atualizar a materia"""
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
        """Salva as atualizações da materia"""
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
        """Deleta a materia"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Materia, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/materias')
        else:
            self.redirect('/login')

    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
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
        ]


class AlunoHandler(Handler):
    """
    Classe responsável pelos Alunos
    """

    def list_ents(self):
        """Renderiza a lista de Alunos"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_alunos.html")
        else:
            self.redirect('/login')

    def list(self):
        """Lista os Alunos e responde com um json"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Aluno.query())
        else:
            self.redirect('/login')

    def view(self):
        """Renderiza a View  para criar um Aluno"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criaraluno.html")
        else:
            self.redirect('/login')

    def post(self):
        """Cria o aluno e salva no banco"""
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
        """Renderiza a View para atualizar o aluno"""
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
        """Salva as atualizações do aluno"""
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
        """Deleta o aluno"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Aluno, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/alunos')
        else:
            self.redirect('/login')

    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
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
        ]


class TurmaHandler(Handler):
    """
    Classe responsável pelas Turmas
    """

    def list_ents(self):
        """Renderiza a lista de Turmas"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_turmas.html")
        else:
            self.redirect('/login')

    def list(self):
        """Lista as Turmas e responde com um json"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Turma.query())
        else:
            self.redirect('/login')

    def view(self):
        """Renderiza a View  para criar uma Turma"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criarturma.html")
        else:
            self.redirect('/login')

    def post(self):
        """Cria a turma e salva no banco"""
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
        """Renderiza a View para atualizar a turma"""
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
        """Salva as atualizações da turma"""
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
        """Deleta a turma"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Turma, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/turmas')
        else:
            self.redirect('/login')

    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
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
        ]


class CursoHandler(Handler):
    """
    Classe responsável pelos Cursos
    """

    def list_ents(self):
        """Renderiza a lista de Cursos"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/listar_cursos.html")
        else:
            self.redirect('/login')

    def list(self):
        """Lista os cursos e responde com um json"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.json_encode(Curso.query())
        else:
            self.redirect('/login')
    
    def view(self):
        """Renderiza a View  para criar um Curso"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            self.render("Admin/criarcurso.html")
        else:
            self.redirect('/login')
    
    def post(self):
        """Cria o curso e salva no banco"""
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
        """Renderiza a View para atualizar o curso"""
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
        """Salva as atualizações do curso"""
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
        """Deleta o curso"""
        id_admin = self.session.get('admin', '')
        if id_admin:
            ndb.Key(Curso, int(id)).delete()
            time.sleep(.1)
            self.redirect('/admin/cursos')
        else:
            self.redirect('/login')

    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
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
        ]


class RelatorioHandler(Handler):
    """
    Classe responsável pelos Relatorios
    """

    def list_ents(self):
        """Renderiza a lista de Relatorios"""
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
        """Lista os relatorios e responde com um json"""
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
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
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
        ]


class LogoutHandler(Handler):
    """
    Classe responsável pelo LogOut
    """
    
    def get(self):
        if self.session:
            if self.session.get('admin',''):
                self.session.pop('admin')
            elif self.session.get('aluno',''):
                self.session.pop('aluno')
        self.redirect('/')
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='logout.get',
                template=r'/logout',
                methods='GET',
                handler=LogoutHandler,
                handler_method='get'
            ),
        ]


class NotFoundPageHandler(Handler):
    """
    Classe responsável pelo Erro 404
    """

    def get(self):
        self.redirect('/')
    
    @staticmethod
    def list_methods():
        """Retorna as rotas possiveis para essa Classe"""
        return [
            Route(
                name='notfoundpagehandler.get',
                template=r'/.*',
                methods='GET',
                handler=NotFoundPageHandler,
                handler_method='get'
            ),
        ]


app = WSGIApplication( # Classe responsvel por administrar as rotas de requisição
    LoginAlunoHandler.list_methods() + \
    AvaliacaoHandler.list_methods() + \
    AvaliacaoPerguntaHandler.list_methods() + \
    CodigoHandler.list_methods() + \
    ProfessorHandler.list_methods() + \
    ValidarCodigo.list_methods() + \
    LoginHandler.list_methods() + \
    FormularioHandler.list_methods() + \
    PerguntaHandler.list_methods() + \
    MateriaHandler.list_methods() + \
    AlunoHandler.list_methods() + \
    TurmaHandler.list_methods() + \
    RelatorioHandler.list_methods() + \
    CursoHandler.list_methods() + \
    LogoutHandler.list_methods() + \
    NotFoundPageHandler.list_methods(),
    config={
        'webapp2_extras.sessions': { #Configurações de sessios
            'secret_key':'b3bdd91a1ffe1e7d9dcd699166efa4c3f2eb8ed9a3921cd95ea4c81fad043b5b',
            'session_max_age':7200,
            }
        }, debug=True)
