

async function load_file() {
  const msg = await window.pywebview.api.READ_file();
  console.log('Message:', msg);
}