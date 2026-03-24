(function () {
  const root = document.getElementById("toss-app");
  if (!root) return;

  const question = root.dataset.question || "";
  const tossBtn = document.getElementById("toss-btn");
  const progress = document.getElementById("progress");
  const status = document.getElementById("status");
  const linesEl = document.getElementById("lines");

  const lines = [];

  const coinLabel = (coin) => (coin === 3 ? "阳" : "阴");

  const renderLines = () => {
    linesEl.innerHTML = "";
    lines.forEach((line, idx) => {
      const item = document.createElement("li");
      const coins = line.coins.map(coinLabel).join("/");
      item.textContent = `第 ${idx + 1} 爻：${line.total}（${line.label}） 硬币：${coins}`;
      linesEl.appendChild(item);
    });
  };

  const createReading = async () => {
    status.textContent = "正在生成卦象...";
    try {
      const resp = await fetch("/api/readings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question, lines }),
      });

      if (!resp.ok) throw new Error("生成失败");
      const data = await resp.json();
      window.location.href = data.url;
    } catch (err) {
      status.textContent = "生成失败，请返回重试";
      tossBtn.disabled = false;
    }
  };

  tossBtn.addEventListener("click", async () => {
    tossBtn.disabled = true;
    status.textContent = "抛掷中...";

    try {
      const resp = await fetch("/api/toss", { method: "POST" });
      if (!resp.ok) throw new Error("抛掷失败");

      const data = await resp.json();
      lines.push({
        position: lines.length + 1,
        coins: data.coins,
      });

      const last = lines[lines.length - 1];
      last.total = data.total;
      last.type = data.type;
      last.label = data.label;

      renderLines();

      if (lines.length >= 6) {
        progress.textContent = "六爻完成";
        status.textContent = "";
        await createReading();
        return;
      }

      progress.textContent = `第 ${lines.length + 1} 次抛掷`;
      status.textContent = `已完成第 ${lines.length} 次`;
      tossBtn.disabled = false;
    } catch (err) {
      status.textContent = "抛掷失败，请重试";
      tossBtn.disabled = false;
    }
  });
})();
