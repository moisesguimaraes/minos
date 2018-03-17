
var turmas;

$(document).ready(function () {
    $.when($.getJSON("/turmas").done(function (data) {
        turmas = data;
    })).done(function () {
        var tam = turmas.length;
        for (var l = 0, i = 0; l < tam; l++ , i++) {
            $("#tbturmas").append(
                '<tr><td>' + turmas[l].user_id + '</td><td>' + turmas[l].periodo + '</td><td><input id="mat' + i + '" type="checkbox" name="turma" value="' + turmas[l].id + '"><label for="mat' + i + '"></label></td></tr>');
        }
        $("#tfmats > tr").append('<td>' + tam + (tam < 2 ? " Turma" : " Turma") + '</td>');
    });
});
