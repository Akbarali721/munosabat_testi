(function () {
    const form = document.getElementById("quiz-form");
    if (!form) return;

    const steps = Array.from(form.querySelectorAll(".quiz-step"));
    const total = steps.length;
    const prevBtn = document.getElementById("quiz-prev");
    const nextBtn = document.getElementById("quiz-next");
    const nav = document.getElementById("quiz-nav");
    const progressLabel = document.getElementById("quiz-progress-label");
    const progressPct = document.getElementById("quiz-progress-pct");
    const progressFill = document.getElementById("quiz-progress-fill");
    const loadingEl = document.getElementById("quiz-loading");
    const loadingText = document.getElementById("loading-text");
    const messages = window.QADAM_LOADING_MESSAGES || [
        "Javoblaringiz tahlil qilinmoqda...",
        "Bir oz sabr — bu bir daqiqadan kam vaqt oladi",
        "Hayotiy vaziyatlar solishtirilmoqda...",
    ];

    let current = 0;
    let nextEnabledTimer = null;

    function pctForStep(index) {
        return Math.max(8, Math.round(((index + 1) / total) * 100));
    }

    function currentStepEl() {
        return steps[current];
    }

    function hasSelection(stepEl) {
        return Boolean(stepEl.querySelector(".qd-option__input:checked"));
    }

    function updateOptionCards(stepEl) {
        stepEl.querySelectorAll(".qd-option").forEach((label) => {
            const input = label.querySelector(".qd-option__input");
            label.classList.toggle("qd-option--selected", input.checked);
        });
    }

    function updateProgress() {
        const number = current + 1;
        const pct = pctForStep(current);
        progressLabel.textContent = `Savol ${number}/${total}`;
        progressPct.textContent = `${pct}%`;
        progressFill.style.width = `${pct}%`;
    }

    function updateNav(forceEnable) {
        const isFirst = current === 0;
        prevBtn.hidden = isFirst;
        prevBtn.disabled = isFirst;
        nav.classList.toggle("qd-nav--solo", isFirst);

        const selected = forceEnable || hasSelection(currentStepEl());
        const isLast = current === total - 1;

        nextBtn.disabled = !selected;
        nextBtn.textContent = isLast ? "Natijani tayyorlash" : "Keyingi →";
        nextBtn.type = isLast && selected ? "submit" : "button";
    }

    function showStep(index) {
        steps.forEach((step, i) => {
            const active = i === index;
            step.classList.toggle("quiz-step--hidden", !active);
            if (active) {
                step.classList.remove("quiz-step--entering");
                void step.offsetWidth;
                step.classList.add("quiz-step--entering");
            }
        });
        current = index;
        updateOptionCards(currentStepEl());
        updateProgress();
        updateNav();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function showLoadingThenSubmit() {
        loadingEl.hidden = false;
        let i = 0;
        loadingText.textContent = messages[0];
        const interval = setInterval(() => {
            i = (i + 1) % messages.length;
            loadingText.textContent = messages[i];
        }, 900);

        setTimeout(() => {
            clearInterval(interval);
            form.submit();
        }, 3200);
    }

    steps.forEach((step) => {
        step.querySelectorAll(".qd-option__input").forEach((input) => {
            input.addEventListener("change", () => {
                updateOptionCards(step);
                if (steps.indexOf(step) !== current) return;

                nextBtn.disabled = true;
                if (nextEnabledTimer) clearTimeout(nextEnabledTimer);
                nextEnabledTimer = setTimeout(() => updateNav(true), 300);
            });
        });
    });

    prevBtn.addEventListener("click", () => {
        if (current > 0) showStep(current - 1);
    });

    nextBtn.addEventListener("click", () => {
        if (nextBtn.type === "submit") return;
        if (!hasSelection(currentStepEl())) return;
        if (current < total - 1) showStep(current + 1);
    });

    form.addEventListener("submit", (event) => {
        const missing = steps.find((step) => !hasSelection(step));
        if (missing) {
            event.preventDefault();
            showStep(steps.indexOf(missing));
            return;
        }
        event.preventDefault();
        showLoadingThenSubmit();
    });

    showStep(0);
})();
