function init_voting () {
    var selected = undefined;
    var help_text = document.getElementById('vote-text');

    function label_on_mouseenter() {
        help_text.innerHTML = this.getAttribute('data-title');
    }

    function label_on_mouseleave() {
        help_text.innerText = '\u00A0';
        if (selected) {
            help_text.innerText = selected.nextSibling.getAttribute('data-title');
        }
    }

    function vote_select () {
        selected = this;
        help_text.innerText = this.nextSibling.getAttribute('data-title');
    }

    function on_form_submit (event) {
        event.preventDefault();

        if (!selected) { return; }

        const data = new FormData();
        data.append(selected.getAttribute('name'), selected.getAttribute('value'));

        fetch(window.location.href, {
            method: 'POST',
            mode: 'same-origin',
            cache: 'no-cache',
            body: data
        }).then( resp => {
            window.location.href = `${window.location.href}/thanks`
        })
    }

    document.querySelectorAll('label.rating-label').forEach(function (element) {
        element.addEventListener("mouseenter", label_on_mouseenter);
        element.addEventListener("mouseleave", label_on_mouseleave);
    });

    document.querySelectorAll('input[name=rating]').forEach(function (element) {
        element.addEventListener("click", vote_select);
    });

    document.getElementById('vote-form').onsubmit = on_form_submit;
}

init_voting();