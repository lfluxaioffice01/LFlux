(function () {
  "use strict";

  const header = document.getElementById("header");
  const navToggle = document.getElementById("navToggle");
  const navMenu = document.getElementById("navMenu");
  const contactForm = document.getElementById("contactForm");

  /* Header scroll effect */
  function onScroll() {
    if (window.scrollY > 40) {
      header.classList.add("header--scrolled");
    } else {
      header.classList.remove("header--scrolled");
    }
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* Mobile navigation */
  navToggle.addEventListener("click", function () {
    const isOpen = navMenu.classList.toggle("active");
    navToggle.classList.toggle("active", isOpen);
    navToggle.setAttribute("aria-expanded", String(isOpen));
    navToggle.setAttribute("aria-label", isOpen ? "메뉴 닫기" : "메뉴 열기");
  });

  document.querySelectorAll(".nav__link, .nav__cta").forEach(function (link) {
    link.addEventListener("click", function () {
      navMenu.classList.remove("active");
      navToggle.classList.remove("active");
      navToggle.setAttribute("aria-expanded", "false");
      navToggle.setAttribute("aria-label", "메뉴 열기");
    });
  });

  /* Scroll reveal animations */
  const revealElements = document.querySelectorAll(".reveal");

  const revealObserver = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
  );

  revealElements.forEach(function (el) {
    revealObserver.observe(el);
  });

  /* Stagger why & service cards */
  document.querySelectorAll(".why-card.reveal").forEach(function (card, i) {
    card.style.transitionDelay = i * 0.1 + "s";
  });

  document.querySelectorAll(".service-card.reveal").forEach(function (card, i) {
    card.style.transitionDelay = i * 0.1 + "s";
  });

  document.querySelectorAll(".portfolio-card.reveal").forEach(function (card, i) {
    card.style.transitionDelay = i * 0.08 + "s";
  });

  /* Contact form — Supabase via /contact */
  if (contactForm) {
    const formStatus = document.getElementById("formStatus");
    const submitBtn = document.getElementById("contactSubmit");

    function showFormStatus(text, isError) {
      if (!formStatus) return;
      formStatus.textContent = text;
      formStatus.hidden = false;
      formStatus.classList.toggle("form-status--error", isError);
      formStatus.classList.toggle("form-status--success", !isError);
    }

    function hideFormStatus() {
      if (!formStatus) return;
      formStatus.hidden = true;
      formStatus.classList.remove("form-status--error", "form-status--success");
    }

    contactForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      hideFormStatus();

      const name = document.getElementById("name").value.trim();
      const email = document.getElementById("email").value.trim();
      const phone = document.getElementById("phone").value.trim();
      const industry = document.getElementById("industry").value.trim();
      const budget = document.getElementById("budget").value;
      const services = Array.from(
        document.querySelectorAll('input[name="service"]:checked')
      ).map(function (el) {
        return el.value;
      });
      const message = document.getElementById("message").value.trim();

      if (submitBtn) {
        submitBtn.disabled = true;
      }

      try {
        const response = await fetch("/contact", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name,
            email: email,
            phone: phone || null,
            industry: industry || null,
            budget: budget || null,
            service_interest: services.length ? services.join(", ") : null,
            message: message,
          }),
        });

        const data = await response.json().catch(function () {
          return {};
        });

        if (!response.ok || data.success === false) {
          showFormStatus("상담 신청 중 오류가 발생했습니다.", true);
          return;
        }

        showFormStatus("상담 신청이 완료되었습니다.", false);
        contactForm.reset();
      } catch (err) {
        showFormStatus("상담 신청 중 오류가 발생했습니다.", true);
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
        }
      }
    });
  }

  /* Active nav link on scroll */
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll(".nav__link");

  function highlightNav() {
    const scrollPos = window.scrollY + 120;

    sections.forEach(function (section) {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute("id");

      if (scrollPos >= top && scrollPos < top + height) {
        navLinks.forEach(function (link) {
          link.classList.remove("nav__link--active");
          if (link.getAttribute("href") === "#" + id) {
            link.classList.add("nav__link--active");
          }
        });
      }
    });
  }

  window.addEventListener("scroll", highlightNav, { passive: true });
})();
