document.addEventListener("DOMContentLoaded", function () {

    const loading = document.getElementById('loading');

    let value = 0;

    if (value == 0) {
        loading1.classList.add('hidden');
    } else {
        loading1.classList.remove('hidden');
    }

    if (value2 == 0) {
        loading2.classList.add('hidden');
    } else {
        loading2.classList.remove('hidden');
    }

    if (value3 == 0) {
        loading3.classList.add('hidden');
    } else {
        loading3.classList.remove('hidden');
    }

});