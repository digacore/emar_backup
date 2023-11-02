const searchInput = document.querySelector("#company-search-input");
if (searchInput) {
  searchInput.addEventListener("keyup", function (e) {
    if (e.key === "Enter") {
      let oldParams = (new URL(window.location)).searchParams;
      let url = new URL(window.location.href);
      url.searchParams.set("q", searchInput.value);
      // reset page to 1
      url.searchParams.set("page", "1");
      url.searchParams.set("per_page", oldParams.get("per_page") || "25");
      url.searchParams.set("from_date", oldParams.get("from_date") || "");
      url.searchParams.set("to_date", oldParams.get("to_date") || "");
      window.location.href = "".concat(url.href);
    }
  });
}

const clearSearchInput = (e) => {
  searchInput.value = "";
  let oldParams = (new URL(window.location)).searchParams;
  let url = new URL(window.location.href);
  url.searchParams.set("q", "");
  // reset page to 1
  url.searchParams.set("page", "1");
  url.searchParams.set("per_page", oldParams.get("per_page") || "25");
  url.searchParams.set("from_date", oldParams.get("from_date") || "");
  url.searchParams.set("to_date", oldParams.get("to_date") || "");
  window.location.href = "".concat(url.href);
}

const applyDateRange = (e) => {
  const fromDateInput = document.querySelector("#from-date-input");
  const toDateInput = document.querySelector("#to-date-input");

  let oldParams = (new URL(window.location)).searchParams;
  let url = new URL(window.location.href);
  url.searchParams.set("q", oldParams.get("q") || "");
  url.searchParams.set("page", "1");
  url.searchParams.set("per_page", oldParams.get("per_page") || "25");
  url.searchParams.set("from_date", fromDateInput.value);
  url.searchParams.set("to_date", toDateInput.value);
  window.location.href = "".concat(url.href);
}

const timeRangeSelector = document.querySelector("#time-range-selector");
timeRangeSelector.addEventListener("change", (e) => {
  const fromDateInput = document.querySelector("#from-date-input");
  const toDateInput = document.querySelector("#to-date-input");

  const today = new Date();

  let startDay = null;
  switch (e.target.value) {
    case "LAST_7": {
      startDay = new Date(new Date().setDate(new Date().getDate() - 7));
      break;
    }
    case "LAST_30": {
      startDay = new Date(new Date().setDate(new Date().getDate() - 30));
      break;
    }
    case "THIS_MONTH": {
      startDay = new Date(new Date().setDate(1));
      break;
    }
    case "THIS_YEAR": {
      startDay = new Date(new Date().setMonth(0, 1));
      break;
    }
    default: {
      startDay = new Date(new Date().setDate(new Date().getDate() - 30));
    }
  }

  fromDateInput.value = startDay.toJSON().split("T")[0];
  toDateInput.value = today.toJSON().split("T")[0];
});
