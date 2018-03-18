
var alunos;

$(document).ready(function () {
    $.when($.getJSON("/alunos").done(function (data) {
        alunos = data;
    })).done(function () {
        var tam = alunos.length;
        for (var l = 0, i=0 ; l < tam; l++, i++) {
            $("#tbalunos").append(
                '<tr><td scope="row">' + alunos[l].matricula + '</td><td>' + alunos[l].nome + '</td><td>' + alunos[l].periodo + '</td><td><input id="aluno' + i + '" type="checkbox" name="aluno" value="' + alunos[l].id + '"><label for="aluno' + i + '"></label></td></tr>');
        }
        $("#tfalunos > tr").append('<td>' + tam + (tam < 2 ? " Aluno" : " Alunos") + '</td>');
    });
});
