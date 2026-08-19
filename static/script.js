document.addEventListener("DOMContentLoaded", function () {

    const dateInput = document.getElementById("expense_date");

    if (dateInput && !dateInput.value) {

        const today = new Date();

        const year = today.getFullYear();

        const month = String(
            today.getMonth() + 1
        ).padStart(2, "0");

        const day = String(
            today.getDate()
        ).padStart(2, "0");

        dateInput.value =
            `${year}-${month}-${day}`;
    }

});