// custom javascript

document.querySelectorAll(".single-search-form").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    await fetch("/search_column", {
      method: "POST",
      body: JSON.stringify({ col_name: e.target.dataset.search_value }),
      headers: {
        "Content-Type": "application/json",
      },
    });
    const globalForm = document.querySelector("#overall-admin-search");
    const globalInput = document.querySelector("#overall-admin-search-input");
    console.log({ globalForm, globalInput });
    globalInput.value = e.target.elements[0].value;
    globalForm.submit();
    // TODO reassign all fields when global search form is submitted
  })
);
