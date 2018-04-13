
var curso;

$(document).ready(function () {
    $.when($.getJSON("/cursos").done(function(data){
        curso = data;
    })).done(function(){
        var tam = curso.length;
        for(var l = 0; l < tam; l++){
            $("#tbcursos").append(
                '<tr><td>' + curso[l].cod + '</td><td>' + curso[l].nome + '</td><td>' + curso[l].descricao + '</td><td><ul class="icons"><li><a href="/curso/'+ curso[l].id + '/view_atualizar" class="icon fa-pencil-square-o"></a></li><li><a href="/curso/'+ curso[l].id + '/apagar" class="icon fa-trash-o"></a></li></ul></td></tr>');
        }
        $("#tfcursos > tr").append('<td>'+ tam + (tam < 2? " Curso" : " Cursos") + '</td>');
    });
});
