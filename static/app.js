"use strict";

let selectedStyle = null;
let selectedRatio = null;
let selectedMode = "standard";
let outFmt = "universal";
let lastResult = null;
const $ = (id) => document.getElementById(id);

async function api(path, opts) {
  const res = await fetch(path, opts);
  return res.json();
}

// ----------------------------- 初始化 -----------------------------
async function loadStyles() {
  const data = await api("/api/styles");
  const styles = data.styles || data;          // 兼容两种返回结构
  const ratios = data.ratios || ["9:16"];
  const modes = data.keyboard_modes || [];
  selectedRatio = data.default_ratio || (ratios[0] || "9:16");
  selectedMode = data.default_mode || "standard";

  const box = $("styleChips");
  box.innerHTML = "";
  styles.forEach((s) => {
    const c = document.createElement("span");
    c.className = "chip";
    c.textContent = s.zh;
    c.onclick = () => {
      selectedStyle = selectedStyle === s.en ? null : s.en;
      document.querySelectorAll("#styleChips .chip").forEach((el) =>
        el.classList.toggle("active", el.textContent === s.zh && selectedStyle === s.en)
      );
    };
    box.appendChild(c);
  });

  const rbox = $("ratioChips");
  rbox.innerHTML = "";
  ratios.forEach((r) => {
    const c = document.createElement("span");
    c.className = "chip" + (r === selectedRatio ? " active" : "");
    c.textContent = r;
    c.onclick = () => {
      selectedRatio = r;
      document.querySelectorAll("#ratioChips .chip").forEach((el) =>
        el.classList.toggle("active", el === c)
      );
    };
    rbox.appendChild(c);
  });

  const mbox = $("modeChips");
  mbox.innerHTML = "";
  modes.forEach((m) => {
    const c = document.createElement("span");
    c.className = "chip" + (m.en === selectedMode ? " active" : "");
    c.textContent = m.zh;
    c.title = m.coverage;
    c.onclick = () => {
      selectedMode = m.en;
      document.querySelectorAll("#modeChips .chip").forEach((el) =>
        el.classList.toggle("active", el === c)
      );
      // 横屏形态自动切到 16:9 比例，体验更顺
      if (m.en === "landscape") {
        selectedRatio = "16:9";
        document.querySelectorAll("#ratioChips .chip").forEach((el) =>
          el.classList.toggle("active", el.textContent === "16:9")
        );
      }
    };
    mbox.appendChild(c);
  });
}

async function loadModels() {
  const data = await api("/api/models");
  const sel = $("model");
  sel.innerHTML = "";
  if (data.ok && data.models.length) {
    data.models.forEach((m) => {
      const o = document.createElement("option");
      o.value = m; o.textContent = m;
      sel.appendChild(o);
    });
  } else {
    const o = document.createElement("option");
    o.value = ""; o.textContent = "（未检测到 Ollama 模型）";
    sel.appendChild(o);
  }
}

async function loadSkins() {
  const list = await api("/api/skins");
  const ul = $("skinList");
  ul.innerHTML = "";
  if (!list.length) {
    ul.innerHTML = '<li style="color:var(--muted)">还没有保存的皮肤</li>';
    return;
  }
  list.forEach((sk) => {
    const li = document.createElement("li");
    li.textContent = sk.description.slice(0, 24) || "(空描述)";
    li.title = sk.description;
    li.onclick = () => {
      $("description").value = sk.description;
      const p = JSON.parse(sk.params || "{}");
      const outs = JSON.parse(sk.outputs || "{}");
      lastResult = {
        zh: "已载入历史皮肤",
        prompt: sk.prompt,
        negative_prompt: sk.negative_prompt,
        params: p,
        outputs: outs,
      };
      $("zh").textContent = lastResult.zh;
      if (p.aspect_ratio) { $("ar").textContent = p.aspect_ratio; $("ar2").textContent = p.aspect_ratio; }
      renderOut();
      $("resultCard").style.display = "block";
    };
    ul.appendChild(li);
  });
}

// ----------------------------- 格式切换 -----------------------------
function renderOut() {
  if (!lastResult) return;
  const outs = lastResult.outputs || {};
  $("outText").value = outs[outFmt] || lastResult.prompt || "";
}

document.querySelectorAll("#fmtTabs .chip").forEach((chip) => {
  chip.onclick = () => {
    outFmt = chip.getAttribute("data-fmt");
    document.querySelectorAll("#fmtTabs .chip").forEach((c) =>
      c.classList.toggle("active", c === chip)
    );
    renderOut();
  };
});

// ----------------------------- 生成 -----------------------------
async function doGenerate() {
  const desc = $("description").value.trim();
  if (!desc) return alert("先写点描述吧～");
  const btn = event.target;
  const old = btn.textContent;
  btn.textContent = "生成中…";
  try {
    const r = await api("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: desc, style: selectedStyle, ratio: selectedRatio, mode: selectedMode }),
    });
    if (!r.ok) return alert(r.error || "生成失败");
    lastResult = r;
    outFmt = "universal";
    document.querySelectorAll("#fmtTabs .chip").forEach((c) =>
      c.classList.toggle("active", c.getAttribute("data-fmt") === "universal")
    );
    $("zh").textContent = r.zh;
    $("ar").textContent = r.params.aspect_ratio;
    $("ar2").textContent = r.params.aspect_ratio;
    $("modeZh").textContent = (r.attributes && r.attributes.mode_zh) || selectedMode;
    // 显示冲突 / 否定等警告
    const wbox = $("warnings");
    const warns = (r.attributes && r.attributes.warnings) || [];
    if (warns.length) {
      wbox.style.display = "block";
      wbox.innerHTML = "⚠️ " + warns.join("<br>⚠️ ");
    } else {
      wbox.style.display = "none";
    }
    renderOut();
    $("resultCard").style.display = "block";
  } catch (e) {
    alert("请求失败：" + e);
  } finally {
    btn.textContent = old;
  }
}

async function doEnhance() {
  if (!lastResult) return alert("请先生成提示词");
  const model = $("model").value;
  if (!model) return alert("未检测到 Ollama 模型，请先安装并 pull 一个模型");
  const btn = event.target;
  const old = btn.textContent;
  btn.textContent = "润色中…";
  try {
    const r = await api("/api/enhance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: lastResult.prompt, model }),
    });
    if (!r.ok) return alert(r.error || "润色失败");
    lastResult.prompt = r.prompt;
    if (lastResult.outputs) lastResult.outputs.universal = r.prompt;
    renderOut();
  } catch (e) {
    alert("请求失败：" + e);
  } finally {
    btn.textContent = old;
  }
}

// ----------------------------- 保存 / 复制 / 导出 / 清空 -----------------------------
async function saveSkin() {
  if (!lastResult) return alert("还没有可保存的结果");
  await api("/api/skins", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      description: $("description").value,
      prompt: lastResult.prompt,
      negative_prompt: lastResult.negative_prompt,
      params: lastResult.params,
      style: selectedStyle || "",
      outputs: lastResult.outputs || {},
    }),
  });
  await loadSkins();
  flash("已保存 ✓");
}

function copyOut() {
  const el = $("outText");
  el.select();
  navigator.clipboard.writeText(el.value).then(
    () => flash("已复制 ✓"),
    () => { document.execCommand("copy"); flash("已复制 ✓"); }
  );
}

async function exportSkins() {
  try {
    const data = await api("/api/export");
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "keyskin_export.json";
    a.click();
    URL.revokeObjectURL(url);
    flash("已导出 ✓");
  } catch (e) {
    alert("导出失败：" + e);
  }
}

function clearAll() {
  $("description").value = "";
  $("outText").value = "";
  $("resultCard").style.display = "none";
  $("warnings").style.display = "none";
  selectedStyle = null;
  selectedMode = "standard";
  outFmt = "universal";
  document.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
  document.querySelectorAll("#fmtTabs .chip").forEach((c) =>
    c.classList.toggle("active", c.getAttribute("data-fmt") === "universal")
  );
  // 复位默认选中的比例与形态 chip
  document.querySelectorAll("#ratioChips .chip").forEach((el) =>
    el.classList.toggle("active", el.textContent === "9:16")
  );
  document.querySelectorAll("#modeChips .chip").forEach((el) =>
    el.classList.toggle("active", el.textContent === "标准全宽")
  );
  selectedRatio = "9:16";
  $("modeZh").textContent = "标准全宽";
}

let flashTimer = null;
function flash(msg) {
  const bar = $("enhanceHint");
  const old = bar.textContent;
  bar.textContent = msg;
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => (bar.textContent = old), 1200);
}

loadStyles();
loadModels();
loadSkins();
