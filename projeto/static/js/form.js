$(document).ready(function() {

	$('form').on('submit', function(event) {

		$.ajax({
			data : {
				contexto : $('#selectSubject option:selected').val()
			},
			type : 'POST',
			url : '/process'
		})
		.done(function(data) {

			if (data.error) {
				$('#title_report').hide();
				$('#errorAlert').text(data.error).show();
				$('#successAlert').hide();
			}
			else {
				$('#title_report').show();
				$('#successAlert').html(data.data).show();
				$('#errorAlert').hide();
			}

		});

		event.preventDefault();

	});

});