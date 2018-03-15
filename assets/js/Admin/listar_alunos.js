 
 var alunos;

 $(document).ready(function () {
    $.when($.getJSON("/alunos").done(function(data){
        alunos = data;
    })).done(function(){
        var tam = alunos.length;
        for(var l = 0; l < tam; l++){
            $("#tbalunos").append(
                '<tr><td scope="row">' + alunos[l].matricula + '</td><td>' + alunos[l].nome + '</td><td>' + alunos[l].periodo + '</td><td><ul class="icons"><li><a href="/aluno/'+ alunos[l].id + '/view_atualizar" class="icon fa-pencil-square-o"></a></li><li><a href="/aluno/'+ alunos[l].id + '/apagar" class="icon fa-trash-o"></a></li></ul></td></tr>');
        }
        $("#tfalunos > tr").append('<td>'+ tam + (tam < 2? " Aluno" : " Alunos") + '</td>');
    });
});
 