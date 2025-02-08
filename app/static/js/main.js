document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    // Spinner
    const spinner = () => {
        setTimeout(() => {
            const spinnerElement = document.querySelector('#spinner');
            if (spinnerElement) {
                spinnerElement.classList.remove('show');
            }
        }, 1);
    };
    spinner();
    
    // Initiate WOW.js (if WOW.js is still in use, include the WOW.js script)
    // If using WOW.js, you don't need to change anything for this part
    new WOW().init();

    // Sticky Navbar
    window.addEventListener('scroll', () => {
        const stickyTop = document.querySelector('.sticky-top');
        if (window.scrollY > 300) {
            stickyTop.classList.add('shadow-sm');
            stickyTop.style.top = '0px';
        } else {
            stickyTop.classList.remove('shadow-sm');
            stickyTop.style.top = '-100px';
        }
    });

    // Back to top button
    window.addEventListener('scroll', () => {
        const backToTop = document.querySelector('.back-to-top');
        if (window.scrollY > 300) {
            backToTop.style.display = 'block';
        } else {
            backToTop.style.display = 'none';
        }
    });

    document.querySelector('.back-to-top').addEventListener('click', (e) => {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Header carousel (using Owl Carousel)
    // If you are still using Owl Carousel, no changes are needed
    $(".header-carousel").owlCarousel({
        autoplay: false,
        animateOut: 'fadeOutLeft',
        items: 1,
        dots: true,
        loop: true,
        nav: true,
        navText: [
            '<i class="bi bi-chevron-left"></i>',
            '<i class="bi bi-chevron-right"></i>'
        ]
    });

    // Testimonials carousel (using Owl Carousel)
    $(".testimonial-carousel").owlCarousel({
        autoplay: false,
        smartSpeed: 1000,
        center: true,
        dots: false,
        loop: true,
        nav: true,
        navText: [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ],
        responsive: {
            0: {
                items: 1
            },
            768: {
                items: 2
            }
        }
    });
});
