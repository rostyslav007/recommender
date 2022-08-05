$(document).ready(function(){
	var current_rating = parseInt($('#rating_bar').attr('data-current_rating'))
	var stars = $('div.rating_star')
	for (var i=0; i<current_rating; i++){
		$(stars[i]).css('background-color', 'yellow')
	}

	if (current_rating == 0){
		$('.rate').text('')
	}
	else {
		$('.rate').text(current_rating)
	}

	$("div.rating_star").hover(function(){
		var number = parseInt($(this).attr('data-rating'))
		$('div.rating_star').each(function(){
			var cd = $(this)
			cd.css('background-color', 'white')
		})
		var stars = $('div.rating_star')

		for (var i=0; i<number; i++){
			$(stars[i]).css('background-color', 'yellow')
		}
		$('.rate').text(number)
	},
	function(){
		$('div.rating_star').each(function(){
			var cd = $(this)
			cd.css('background-color', 'white')
		})
		$('.rate').text('')

		for (var i=0; i<current_rating; i++){
			$(stars[i]).css('background-color', 'yellow')
		}
		if (current_rating == 0){
			$('.rate').text('')
		}
		else {
			$('.rate').text(current_rating)
		}
	})

	$("div.rating_star").on('click', function(){
		var rating = $(this).attr('data-rating')
		var film_id = $(this).attr('data-id')
		var user_id = $(this).attr('data-user_id')
		var server_data = {
			'user_id': user_id,
			'film_id': film_id,
			'rating': rating,
			'current_rating': current_rating
		}

		$.ajax({
		  type: "POST",
		  url: "/rate",
		  data: JSON.stringify(server_data),
		  contentType: "application/json",
		  dataType: 'json',
		  success:function(result) {
		     current_rating = result['new_rating']
		     for (var i=0; i<current_rating; i++){
				$(stars[i]).css('background-color', 'yellow')
			}
		     $('.rate').text(current_rating)
		  } 
		});
	})
})