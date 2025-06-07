var slideIndex = 1;
showSlides(slideIndex);

// Next/previous controls
function moveSlide(n) {
  showSlides(slideIndex += n);
}

// Thumbnail image controls
function currentSlide(n) {
showSlides(slideIndex = n);
}

function showSlides(n) {
  var i;
  var slides = document.getElementsByClassName("carousel-slide");
  var dots = document.getElementsByClassName("dot");

  if (n > slides.length) {slideIndex = 1}
  if (n < 1) {slideIndex = slides.length}

  // Hide all slides
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
  }

  // Remove the "active" class from all dots
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }

  // Show the current slide and add "active" class to the corresponding dot
  slides[slideIndex-1].style.display = "block";  
  dots[slideIndex-1].className += " active";
}

document.querySelector('.hero-carousel').addEventListener('touchmove', function(e) {
  // Determine swipe direction
  var touch = e.touches[0];
  var change = touch.clientX - touchStartX; // touchStartX is where the swipe started
  var isHorizontalSwipe = Math.abs(change) > Math.abs(touch.clientY - touchStartY);

  // Prevent vertical scrolling if it's a horizontal swipe
  if (isHorizontalSwipe) {
      e.preventDefault();
  }
}, { passive: false });


// Optional: Add auto-slide functionality
var slideInterval = setInterval(function() { moveSlide(1); }, 3000); // Change image every 3 seconds
