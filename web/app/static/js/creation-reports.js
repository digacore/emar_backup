// Tooltips initialization
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

// Reloading function
const autoReload = (shouldReload) => {
  setTimeout(() => {
    if (shouldReload) {
      window.location.reload();
    }
  }, 5000);
}

// Searching input
const searchInput = document.querySelector("#reports-search-input");
if (searchInput) {
  searchInput.addEventListener("keyup", function (e) {
    if (e.key === "Enter") {
      let oldParams = (new URL(window.location)).searchParams;
      let url = new URL(window.location.href);
      url.searchParams.set("q", searchInput.value);
      // reset page to 1
      url.searchParams.set("page", "1");
      url.searchParams.set("per_page", oldParams.get("per_page") || "25");
      url.searchParams.set("approved_page", oldParams.get("approved_page") || "False");
      window.location.href = "".concat(url.href);
    }
  });
}

// X button to clear search input
const clearSearchInput = (e) => {
  searchInput.value = "";
  let oldParams = (new URL(window.location)).searchParams;
  let url = new URL(window.location.href);
  url.searchParams.set("q", "");
  // reset page to 1
  url.searchParams.set("page", "1");
  url.searchParams.set("per_page", oldParams.get("per_page") || "25");
  url.searchParams.set("approved_page", oldParams.get("approved_page") || "False");
  window.location.href = "".concat(url.href);
}


// Function for handling changes in reports (delete action; set downloading type)
const handleChangeData = async (obj_id, changed_data, csrf_token) => {
  const url = new URL(`/pcc/creation-reports/${obj_id}`, window.location.origin).href;
  const newData = new FormData();
  for (const [key, value] of Object.entries(changed_data)) {
    newData.append(key, JSON.stringify(value));
  }
  newData.append('csrf_token', csrf_token);

  try {
    response = await fetch(url, {
      method: 'POST',
      body: newData,
    });

    if (response.status !== 200) {
      throw new Error(`Unsuccessful change of report data: ${response.status}`);
    }

  } catch (error) {
    alert(`Error while changing report data: ${error}`);
  }

  window.location.reload();
}
