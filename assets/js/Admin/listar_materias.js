 
 var mats;

 $(document).ready(function () {
    $.when($.getJSON("/materias").done(function(data){
        mats = data;
    })).done(function(){
        var tam = mats.length;
        for(var l = 0; l < tam; l++){
            $("#tbmats").append(
                '<tr><td>' + mats[l].user_id + '</td><td>' + mats[l].titulo + '</td><td>' + mats[l].periodo + '</td><td><ul class="icons"><li><a href="/materia/'+ mats[l].id + '/view_atualizar" class="icon fa-pencil-square-o"></a></li><li><a href="/materia/'+ mats[l].id + '/apagar" class="icon fa-trash-o"></a></li></ul></td></tr>');
        }
        $("#tfmats > tr").append('<td>'+ tam + (tam < 2? " Matéria" : " Matérias") + '</td>');
    });
});
 