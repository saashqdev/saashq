// Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

saashq.ready(function() {

	if(saashq.utils.get_url_arg('subject')) {
	  $('[name="subject"]').val(saashq.utils.get_url_arg('subject'));
	}

	$('.btn-send').off("click").on("click", function() {
		var email = $('[name="email"]').val();
		var message = $('[name="message"]').val();

		if(!(email && message)) {
			saashq.msgprint('{{ _("Please enter both your email and message so that we can get back to you. Thanks!") }}');
			return false;
		}

		if(!validate_email(email)) {
			saashq.msgprint('{{ _("You seem to have written your name instead of your email. Please enter a valid email address so that we can get back.") }}');
			$('[name="email"]').focus();
			return false;
		}

		$("#contact-alert").toggle(false);
		saashq.call({
			type: "POST",
			method: "saashq.www.contact.send_message",
			args: {
				subject: $('[name="subject"]').val(),
				sender: email,
				message: message,
			},
			callback: function(r) {
				if (!r.exc) {
					saashq.msgprint('{{ _("Thank you for your message") }}', '{{ _("Message Sent") }}');
				}
				$(':input').val('');
			},
		});
	});
});

var msgprint = function(txt) {
	if(txt) $("#contact-alert").html(txt).toggle(true);
}
