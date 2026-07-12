(function () {
    const copyBtn = document.getElementById("premium-copy-btn");
    const textarea = document.getElementById("premium-share-text");
    if (!copyBtn || !textarea) return;

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
})();
