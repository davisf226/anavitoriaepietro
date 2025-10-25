window.addEventListener('scroll', () => {
  const navbar = document.getElementById('navbar');
  if (window.scrollY > 100) {
    navbar.classList.add('fixed');
  } else {
    navbar.classList.remove('fixed');
  }
});

// ===== CARROSSEL COM AUTO TROCA =====
let currentIndex = 0;
let autoSlideInterval;

function changeImage(thumb, manual = true) {
  const mainImage = document.getElementById("mainImage");
  const thumbs = document.querySelectorAll(".thumb");
  const newSrc = thumb.src;

  thumbs.forEach(img => img.classList.remove("active"));
  thumb.classList.add("active");

  mainImage.classList.remove("show");
  setTimeout(() => {
    mainImage.src = newSrc;
    mainImage.classList.add("show");
  }, 200);

  if (manual) {
    restartAutoSlide();
  }
}

function startAutoSlide() {
  const thumbs = document.querySelectorAll(".thumb");
  autoSlideInterval = setInterval(() => {
    currentIndex = (currentIndex + 1) % thumbs.length;
    changeImage(thumbs[currentIndex], false);
  }, 4000);
}

function restartAutoSlide() {
  clearInterval(autoSlideInterval);
  startAutoSlide();
}

window.addEventListener("DOMContentLoaded", () => {
  const mainImage = document.getElementById("mainImage");
  const thumbs = document.querySelectorAll(".thumb");

  mainImage.classList.add("show");

  // Marca o primeiro como ativo
  thumbs[0].classList.add("active");

  // Inicia auto slide
  startAutoSlide();
});
