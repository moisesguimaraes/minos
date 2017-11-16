$(document).ready(function () {
    var i = 1;
    $('#add_radio').click(function () {
        i++;
        $("#formul").show();
        $('#tabb').append('<tr id="qq' + i + '"><td><h3>Questao</h3></td><td id="td1"><label id="q' + i + '">Enunciado:<input id="q' + i + '" type="text" name="enunciado" /></label><div><table><tbody id="respostas"><tr id="res' + i + '" class="icons"><td class="icon fa-check-circle-o"></td><td><input id="r' + i + '" type="text" name="resposta" /></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_add_line">ADD</button></td></tr></tbody></table></div></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove">X</button></td><input type="hidden" name="tipo" value="2"></tr>');
        $("#botoes1").toggle();
    });
    $('#add_texto').click(function () {
        i++;
        $("#formul").show();
        $('#tabb').append('<tr id="qq' + i + '"><td><h3>Questao</h3></td><td id="td1"><label id="q' + i + '">Enunciado:<input id="q' + i + '" type="text" name="enunciado" /></label></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove">X</button></td><input type="hidden" name="tipo" value="1"><input type="hidden" name="resposta" value="-"></tr>');
        $("#botoes1").hide();
    });
    $('#add_marcar').click(function () {
        i++;
        $("#formul").show();
        $('#tabb').append('<tr id="qq' + i + '"><td><h3>Questao</h3></td><td id="td1"><label id="q' + i + '">Enunciado:<input id="q' + i + '" type="text" name="enunciado" /></label><div><table><tbody id="respostas"><tr id="res' + i + '" class="icons"><td class="icon fa-check-square-o"></td><td><input id="r' + i + '" type="text" name="resposta" /></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_add_line">ADD</button></td></tr></tbody></table></div></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove">X</button></td><input type="hidden" name="tipo" value="3"></tr>');
        $("#botoes1").hide();
    });
    $(document).on('click', '.btn_remove', function () {
        var button_id = $(this).attr("id");
        $('#qq' + button_id + '').remove();
        $("#botoes1").show();
    });
    $(document).on('click', '.btn_remove_line', function () {
        var button_id = $(this).attr("id");
        $('#res' + button_id + '').remove();
    });
    $(document).on('click', '.btn_add_line', function () {
        i++;
        $("#respostas").append('<tr id="res' + i + '" class="icons"><td class="icon fa-check-circle-o"></td><td><input id="r' + i + '" type="text" name="resposta" /></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove_line">X</button><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_add_line">ADD</button></td></tr>');
    });
    $('#submit').click(function () {
        $.ajax({
            url: "/teste",
            method: "POST",
            data: $('#add_name').serialize(),
            success: function (data) {
                alert(data);
                $('#add_name')[0].reset();
            }
        });
    });
});
