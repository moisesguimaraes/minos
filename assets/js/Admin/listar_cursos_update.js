
var cursos;

$(document).ready(function () {
    $.when($.getJSON("/cursos").done(function (data) {
        cursos = data;
    })).done(function () {
        var tam = cursos.length;
        for (var l = 0, i=0 ; l < tam; l++, i++) {
            $("#tbcursos").append(
                '<tr><td scope="row">' + cursos[l].cod + '</td><td>' + cursos[l].nome + '</td><td>' + cursos[l].descricao + '</td><td><input id="curso' + i + '" type="checkbox" name="curso" value="' + cursos[l].id + '"><label for="curso' + i + '"></label></td></tr>');
        }
        $("#tfcursos > tr").append('<td>' + tam + (tam < 2 ? " Curso" : " Cursos") + '</td>');
    });
});
