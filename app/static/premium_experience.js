(function () {
    const splash = document.getElementById("premium-splash");
    const experience = document.getElementById("premium-experience");
    const copyBtn = document.getElementById("premium-copy-btn");
    const textarea = document.getElementById("premium-share-text");

    if (splash && experience) {
        setTimeout(() => {
            splash.classList.add("qd-premium-splash--out");
            setTimeout(() => {
                splash.hidden = true;
                experience.hidden = false;
                experience.classList.add("qd-premium-experience--visible");
                initScrollReveal();
            }, 500);
        }, 1600);
    } else {
        initScrollReveal();
    }

    if (copyBtn && textarea) {
        copyBtn.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(textarea.value);
                const original = copyBtn.textContent;
                copyBtn.textContent = "Nusxalandi ✓";
                setTimeout(() => {
                    copyBtn.textContent = original;
                }, 2000);
            } catch {
                textarea.select();
                document.execCommand("copy");
            }
        });
    }

    function initScrollReveal() {
        const sections = document.querySelectorAll("[data-premium-section]");
        if (!sections.length || !("IntersectionObserver" in window)) {
            sections.forEach((el) => el.classList.add("qd-premium-section--visible"));
            animateMapBars();
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("qd-premium-section--visible");
                        if (entry.target.querySelector("[data-map-fill]")) {
                            animateMapBars();
                        }
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
        );

        sections.forEach((section) => observer.observe(section));
    }

    function animateMapBars() {
        document.querySelectorAll("[data-map-percent]").forEach((item) => {
            const fill = item.querySelector("[data-map-fill]");
            if (!fill || fill.dataset.animated === "1") return;
            const target = item.getAttribute("data-map-percent") || "0";
            fill.dataset.animated = "1";
            requestAnimationFrame(() => {
                fill.style.width = `${target}%`;
            });
        });
    }
})();
