
var forms;

$(document).ready(function () {
    $.when($.getJSON("/formularios").done(function(data){
        forms = data;
    })).done(function(){
        var tam = forms.length;
        for(var l = 0, i=0; l < tam; l++, i++){
            $("#tbforms").append(
                '<tr><td>' + forms[l].user_id + '</td><td>' + forms[l].titulo + '</td><td>' + forms[l].descricao + '</td><td><input id="form' + i + '" type="checkbox" name="formulario" value="' + forms[l].id +'"><label for="form' + i + '"></label></td></tr>');
        }
        $("#tfforms > tr").append('<td>'+ tam + (tam < 2? " Formulário" : " Formulários") + '</td>');
    });
});
