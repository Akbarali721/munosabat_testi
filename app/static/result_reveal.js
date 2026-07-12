(function () {
    const intro = document.getElementById("result-intro");
    const details = document.getElementById("result-details");
    const continueBtn = document.getElementById("result-continue-btn");
    const config = window.QADAM_RESULT || {};
    const storageKey = config.sessionId
        ? `qadam_result_stage_${config.sessionId}`
        : "qadam_result_stage";

    if (!intro || !details || !continueBtn) return;

    function showDetails(smooth) {
        intro.hidden = true;
        details.hidden = false;
        details.classList.add("qd-result-details--visible");
        try {
            sessionStorage.setItem(storageKey, "details");
        } catch (_) {
            /* ignore */
        }
        if (smooth) {
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    }

    function showIntro() {
        intro.hidden = false;
        details.hidden = true;
        details.classList.remove("qd-result-details--visible");
    }

    let saved = null;
    try {
        saved = sessionStorage.getItem(storageKey);
    } catch (_) {
        saved = null;
    }

    if (config.opened || saved === "details") {
        showDetails(false);
    } else {
        showIntro();
    }

    continueBtn.addEventListener("click", () => {
        showDetails(true);
    });
})();
