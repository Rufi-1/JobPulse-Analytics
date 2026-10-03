document.addEventListener('DOMContentLoaded', function () {
  // Mobile nav toggle
  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('mainNav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var isOpen = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  }

  // Auto-dismiss alerts after a few seconds
  document.querySelectorAll('.alert').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 6000);
  });

  // Confirm before submitting any form marked data-confirm="message"
  // (used for logout and other actions worth a second thought).
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      var message = form.getAttribute('data-confirm');
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // AJAX save/unsave job buttons: <button class="js-save-toggle" data-url="...">
  document.querySelectorAll('.js-save-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var url = btn.getAttribute('data-url');
      var csrfToken = getCookie('csrftoken');

      fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken,
        },
      })
        .then(function (response) { return response.json(); })
        .then(function (data) {
          if (data.saved) {
            btn.textContent = '★ Saved';
            btn.classList.add('btn-outline');
          } else {
            btn.textContent = '☆ Save job';
            btn.classList.remove('btn-outline');
          }
        })
        .catch(function () {
          window.location.reload();
        });
    });
  });

  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
