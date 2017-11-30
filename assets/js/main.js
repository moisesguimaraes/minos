/*
	Atmosphere by Pixelarity
	pixelarity.com | hello@pixelarity.com
	License: pixelarity.com/license
*/

(function($) {

	skel.breakpoints({
		xlarge:	'(max-width: 1680px)',
		large: '(max-width: 1280px)',
		medium: '(max-width: 980px)',
		small: '(max-width: 736px)',
		xsmall: '(max-width: 480px)',
		xxsmall: '(max-width: 360px)'
	});

	$(function() {

		var	$window = $(window),
			$body = $('body'),
			$header = $('#header'),
			$banner = $('#banner');

		// Disable animations/transitions until the page has loaded.
			$body.addClass('is-loading');

			$window.on('load', function() {
				window.setTimeout(function() {
					$body.removeClass('is-loading');
				}, 100);
			});

		// Fix: Placeholder polyfill.
			$('form').placeholder();

		// Prioritize "important" elements on medium.
			skel.on('+medium -medium', function() {
				$.prioritize(
					'.important\\28 medium\\29',
					skel.breakpoint('medium').active
				);
			});

		// Scrolly.
			$('.scrolly').scrolly({
				offset: function() {
					return $header.height();
				}
			});

		// Header.
			if (skel.vars.IEVersion < 9)
				$header.removeClass('alt');

			if ($banner.length > 0
			&&	$header.hasClass('alt')) {

				$window.on('resize', function() { $window.trigger('scroll'); });

				$banner.scrollex({
					bottom:		$header.outerHeight(),
					terminate:	function() { $header.removeClass('alt'); },
					enter:		function() { $header.addClass('alt'); },
					leave:		function() { $header.removeClass('alt'); }
				});

			}

		// Menu.
			var $menu = $('#menu');

			$menu._locked = false;

			$menu._lock = function() {

				if ($menu._locked)
					return false;

				$menu._locked = true;

				window.setTimeout(function() {
					$menu._locked = false;
				}, 350);

				return true;

			};

			$menu._show = function() {

				if ($menu._lock())
					$body.addClass('is-menu-visible');

			};

			$menu._hide = function() {

				if ($menu._lock())
					$body.removeClass('is-menu-visible');

			};

			$menu._toggle = function() {

				if ($menu._lock())
					$body.toggleClass('is-menu-visible');

			};

			$menu
				.appendTo($body)
				.on('click', function(event) {

					event.stopPropagation();

					// Hide.
						$menu._hide();

				})
				.find('.inner')
					.on('click', '.close', function(event) {

						event.preventDefault();
						event.stopPropagation();
						event.stopImmediatePropagation();

						// Hide.
							$menu._hide();

					})
					.on('click', function(event) {
						event.stopPropagation();
					})
					.on('click', 'a', function(event) {

						var href = $(this).attr('href');

						event.preventDefault();
						event.stopPropagation();

						// Hide.
							$menu._hide();

						// Redirect.
							window.setTimeout(function() {
								window.location.href = href;
							}, 350);

					});

			$body
				.on('click', 'a[href="#menu"]', function(event) {

					event.stopPropagation();
					event.preventDefault();

					// Toggle.
						$menu._toggle();

				})
				.on('keydown', function(event) {

					// Hide on escape.
						if (event.keyCode == 27)
							$menu._hide();

				});


	});

})(jQuery);

/* Edmilson */
$(document).ready(function () {
    var i = 1;
    $('#add_radio').click(function () {
        i++;
        $("#formul").show();
        $('#tabb').append('<tr id="qq' + i + '"><td><h3>Questao</h3></td><td id="td1"><label id="q' + i + '">Enunciado:<input id="q' + i + '" autofocus type="text" name="enunciado" /></label><div><table><tbody id="respostas"><tr id="res' + i + '" class="icons"><td class="icon fa-check-circle-o"></td><td><input id="r' + i + '" type="text" name="resposta" /></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_add_line1">ADD</button></td></tr></tbody></table></div></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove">X</button></td><input type="hidden" name="tipo" value="2"></tr>');
        $("#botoes1").hide();
    });
    $('#add_texto').click(function () {
        i++;
        $("#formul").show();
        $('#tabb').append('<tr id="qq' + i + '"><td><h3>Questao</h3></td><td id="td1"><label id="q' + i + '">Enunciado:<input id="q' + i + '" autofocus type="text" name="enunciado" /></label></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove">X</button></td><input type="hidden" name="tipo" value="1"><input type="hidden" name="resposta" value="-"></tr>');
        $("#botoes1").hide();
    });
    $('#add_marcar').click(function () {
        i++;
        $("#formul").show();
        $('#tabb').append('<tr id="qq' + i + '"><td><h3>Questao</h3></td><td id="td1"><label id="q' + i + '">Enunciado:<input id="q' + i + '" autofocus type="text" name="enunciado" /></label><div><table><tbody id="respostas"><tr id="res' + i + '" class="icons"><td class="icon fa-check-square-o"></td><td><input id="r' + i + '" type="text" name="resposta" /></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_add_line2">ADD</button></td></tr></tbody></table></div></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove">X</button></td><input type="hidden" name="tipo" value="3"></tr>');
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
    $(document).on('click', '.btn_add_line1', function () {
        i++;
        $("#respostas").append('<tr id="res' + i + '" class="icons"><td class="icon fa-check-circle-o"></td><td><input id="r' + i + '" type="text" name="resposta" /></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove_line">X</button><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_add_line">ADD</button></td></tr>');
    });
    $(document).on('click', '.btn_add_line2', function () {
        i++;
        $("#respostas").append('<tr id="res' + i + '" class="icons"><td class="icon fa-check-square-o"></td><td><input id="r' + i + '" type="text" name="resposta" /></td><td><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_remove_line">X</button><button type="button" name="remove" id="' + i + '" class="btn btn-danger btn_add_line">ADD</button></td></tr>');
    });
});

function copytoclipboard(element) {
    var copyTextarea = document.querySelector(element);
    copyTextarea.select();
    try {
        var successful = document.execCommand('copy');
        var msg = successful ? 'copiado' : 'não copiado';
        window.alert('Codigo ' + msg + '!');
    } catch (err) {
        window.alert('Oops, incapaz de copiar!');
    }
};