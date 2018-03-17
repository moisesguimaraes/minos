 
 var turmas;

 $(document).ready(function () {
    $.when($.getJSON("/turmas").done(function(data){
        turmas = data;
    })).done(function(){
        var tam = turmas.length;
        for(var l = 0; l < tam; l++){
            $("#tbturmas").append(
                '<tr><td>' + turmas[l].user_id + '</td><td>' + turmas[l].periodo + '</td><td><ul class="icons"><li><a href="/turma/'+ turmas[l].id + '/view_atualizar" class="icon fa-pencil-square-o"></a></li><li><a href="/turma/'+ turmas[l].id + '/apagar" class="icon fa-trash-o"></a></li></ul></td></tr>');
        }
        $("#tfturmas > tr").append('<td>'+ tam + (tam < 2? " Turma" : " Turmas") + '</td>');
    });
});
 