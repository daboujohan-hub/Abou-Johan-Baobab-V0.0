let pyodide = null;
self.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.type === "init") {
      importScripts(m.pyodideUrl);
      pyodide = await loadPyodide({ indexURL: m.indexURL });
      const mk = (d) => { try { pyodide.FS.mkdir(d); } catch (_) {} };
      mk("/baobab_src");
      for (const [chemin, texte] of Object.entries(m.sources)) {
        let cur = "/baobab_src";
        for (const part of chemin.split("/").slice(0, -1)) { cur += "/" + part; mk(cur); }
        pyodide.FS.writeFile("/baobab_src/" + chemin, texte);
      }
      pyodide.runPython(m.harnais);
      self.lancer = pyodide.globals.get("lancer_baobab");
      self.postMessage({ type: "pret" });
    } else if (m.type === "run") {
      const sortie = self.lancer(m.code);
      self.postMessage({ type: "fini", id: m.id, sortie: sortie });
    }
  } catch (err) {
    self.postMessage({ type: "erreur", id: m.id, message: String(err) });
  }
};
