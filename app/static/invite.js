(function () {
    const copyBtn = document.getElementById("copy-btn");
    const input = document.getElementById("invite-url");
    if (!copyBtn || !input) return;

    copyBtn.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(input.value);
            const original = copyBtn.textContent;
            copyBtn.textContent = "Nusxalandi ✓";
            setTimeout(() => {
                copyBtn.textContent = original;
            }, 2000);
        } catch {
            input.select();
            document.execCommand("copy");
        }
    });
})();
