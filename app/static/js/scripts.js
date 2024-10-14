// scripts.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript is ready!');

    // Example: Highlight the selected answer on the exam page
    const radioGroups = document.querySelectorAll('.radio-group');

    radioGroups.forEach(group => {
        const radios = group.querySelectorAll('input[type="radio"]');
        radios.forEach(radio => {
            radio.addEventListener('change', function() {
                radios.forEach(r => r.parentNode.classList.remove('selected'));
                if (this.checked) {
                    this.parentNode.classList.add('selected');
                }
            });
        });
    });
});
