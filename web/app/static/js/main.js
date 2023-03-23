// custom javascript

document.querySelectorAll(".single-search-form").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    await fetch("/search_column", {
      method: "POST",
      body: JSON.stringify({
        col_name: e.target.dataset.search_value,
        current_href: window.location.href,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    });
    const globalForm = document.querySelector("#overall-admin-search");
    const globalInput = document.querySelector("#overall-admin-search-input");
    globalInput.value = e.target.elements[0].value;
    globalForm.submit();
  })
);

document.querySelectorAll("#overall-admin-search").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    await fetch("/search_column", {
      method: "POST",
      body: JSON.stringify({
        col_name: "all",
        current_href: window.location.href,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    });
    const globalForm = document.querySelector("#overall-admin-search");
    globalForm.submit();
  })
);
