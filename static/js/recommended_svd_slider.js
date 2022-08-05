$(document).ready(function(){
	var recommended_films = $('.recommended_film_svd')
	var film_count = recommended_films.length
	var overflow_width = $('#recommended_for_you_svd').prop('scrollWidth')
	var width = $('#recommended_for_you_svd').width()
	var left_arrow = $('.left_arrow_svd')
	var right_arrow = $('.right_arrow_svd')
	var overflow_index = -1
	var bar = $('.slider_svd')
	var img_width = $('#recommended_for_you_svd img').width()

	if (film_count < 8){
		left_arrow.css('display', 'none')
		right_arrow.css('display', 'none')
	} 

	for (var i=0; i<film_count; i++){
		elem = $(recommended_films[i])
		var offset = elem.offset().left;
		if (elem.position().left + offset > width) {
			overflow_index = i + 2
			break
		}
	}

	var count = film_count - overflow_index 
	overflow_index = 0
	
	$(right_arrow).click(function(){
		var margin = parseInt($(bar).css('left').replace('px', ''))
		overflow_index += 1
		p = margin
		if (overflow_index >= count){
			overflow_index = count - 1
		} else {
			p -= img_width
		}
		$(bar).css('left', p + 'px')
	})

	$(left_arrow).click(function(){
		console.log('1')
		var margin = parseInt($(bar).css('left').replace('px', ''))
		overflow_index -= 1
		p = margin
		if (overflow_index < 0){
			overflow_index = 0
		} else {
			p += img_width
		}
		$(bar).css('left', p + 'px')
	})

})