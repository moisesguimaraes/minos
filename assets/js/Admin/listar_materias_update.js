 
 var mats;

 $(document).ready(function () {
    $.when($.getJSON("/materias").done(function(data){
        mats = data;
    })).done(function(){
        var tam = mats.length;
        for(var l = 0, i = 0; l < tam; l++, i++){
            $("#tbmats").append(
                '<tr><td>' + mats[l].user_id + '</td><td>' + mats[l].titulo + '</td><td>' + mats[l].periodo + '</td><td><input id="mat' + i + '" type="checkbox" name="materia" value="' + mats[l].id +'"><label for="mat' + i + '"></label></td></tr>');
        }
        $("#tfmats > tr").append('<td>'+ tam + (tam < 2? " Matéria" : " Matérias") + '</td>');
    });
});
 