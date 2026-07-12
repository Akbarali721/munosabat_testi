(function () {
    const form = document.getElementById("start-form");
    if (!form) return;

    const submitBtn = document.getElementById("start-submit");
    const scrollBtn = document.getElementById("start-scroll-btn");
    const formSection = document.getElementById("start-form-section");
    const initDataInput = document.getElementById("init_data");

    const tg = window.Telegram && window.Telegram.WebApp;
    if (tg) {
        tg.ready();
        tg.expand();
        if (initDataInput && tg.initData) {
            initDataInput.value = tg.initData;
        }
    }

    function syncChipState(label) {
        const input = label.querySelector('input[type="radio"]');
        const body = label.querySelector(".qd-chip__body, .qd-stage__body");
        if (body && input) {
            body.classList.toggle("is-selected", input.checked);
        }
    }

    function validateForm() {
        const name = form.querySelector("#name");
        const gender = form.querySelector('input[name="gender"]:checked');
        const stage = form.querySelector('input[name="relationship_stage"]:checked');
        submitBtn.disabled = !(name && name.value.trim() && gender && stage);
    }

    if (scrollBtn && formSection) {
        scrollBtn.addEventListener("click", () => {
            formSection.scrollIntoView({ behavior: "smooth", block: "start" });
            setTimeout(() => form.querySelector("#name")?.focus(), 400);
        });
    }

    form.querySelectorAll(".qd-chip, .qd-stage").forEach((label) => {
        label.addEventListener("click", () => {
            setTimeout(() => {
                form.querySelectorAll(".qd-chip, .qd-stage").forEach(syncChipState);
                validateForm();
            }, 0);
        });
    });

    form.querySelector("#name").addEventListener("input", validateForm);
    form.addEventListener("submit", () => {
        if (tg && initDataInput && tg.initData) {
            initDataInput.value = tg.initData;
        }
    });
    validateForm();
})();
