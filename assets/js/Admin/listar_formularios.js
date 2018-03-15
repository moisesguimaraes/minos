
var forms;

$(document).ready(function () {
    $.when($.getJSON("/formularios").done(function(data){
        forms = data;
    })).done(function(){
        var tam = forms.length;
        for(var l = 0; l < tam; l++){
            $("#tbforms").append(
                '<tr><td>' + forms[l].user_id + '</td><td>' + forms[l].titulo + '</td><td>' + forms[l].descricao + '</td><td><ul class="icons"><li><a href="/formulario/'+ forms[l].id + '/view_atualizar" class="icon fa-pencil-square-o"></a></li><li><a href="/formulario/'+ forms[l].id + '/apagar" class="icon fa-trash-o"></a></li></ul></td></tr>');
        }
        $("#tfforms > tr").append('<td>'+ tam + (tam < 2? " Formulário" : " Formulários") + '</td>');
    });
});
