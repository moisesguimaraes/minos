  
 var pergs;

 $(document).ready(function () {
    $.when($.getJSON("/perguntas").done(function(data){
        pergs = data;
    })).done(function(){
        var tam = pergs.length;
        for(var l = 0, i = 0; l < tam; l++, i++){
            $("#tbpergs").append(
                '<tr><td>' + pergs[l].user_id + '</td><td>' + pergs[l].enunciado + '</td><td>' + pergs[l].tipo + '</td><td><input id="form' + i + '" type="checkbox" name="pergunta" value="' + pergs[l].id +'"><label for="form' + i + '"></label></td></tr>');
        }
        $("#tfpergs > tr").append('<td>'+ tam + (tam < 2? "  Pergunta" : "  Perguntas") + '</td>');
    });
});
 