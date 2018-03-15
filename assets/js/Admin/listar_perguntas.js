  
 var pergs;

 $(document).ready(function () {
    $.when($.getJSON("/perguntas").done(function(data){
        pergs = data;
    })).done(function(){
        var tam = pergs.length;
        for(var l = 0; l < tam; l++){
            $("#tbpergs").append(
                '<tr><td>' + pergs[l].user_id + '</td><td>' + pergs[l].enunciado + '</td><td>' + pergs[l].tipo + '</td><td><ul class="icons"><li><a href="/pergunta/'+ pergs[l].id + '/view_atualizar" class="icon fa-pencil-square-o"></a></li><li><a href="/pergunta/'+ pergs[l].id + '/apagar" class="icon fa-trash-o"></a></li></ul></td></tr>');
        }
        $("#tfpergs > tr").append('<td>'+ tam + (tam < 2? "  Pergunta" : "  Perguntas") + '</td>');
    });
});
 