document.addEventListener("DOMContentLoaded", async function () {
  const editCompanySelector = document.getElementById("company");
  const editLocationSelector = document.getElementById("location");
  const addLocationSelector = document.getElementById("additional_locations");
  let additionalLocations = [];
  //   if first two selectors empty return
  if (
    editCompanySelector.value == "__None" ||
    editLocationSelector.value == "__None"
  ) {
    return;
  } else if (addLocationSelector) {
    const urlParams = new URLSearchParams(window.location.search);
    const computerId = urlParams.get("id");
    const res = await fetch(`/location/${computerId}/additional_locations`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.additional_locations) {
          addLocationSelector.querySelectorAll("option").forEach((option) => {
            if (data.additional_locations.includes(Number(option.value))) {
              additionalLocations.push(option.textContent);
            }
          });
          return additionalLocations;
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
    addLocationSelector.querySelectorAll("option").forEach((option) => {
      if (res.includes(option.textContent.trim())) {
        option.selected = true;
        const ul = document.querySelector(".select2-choices");
        const li = document.createElement("li");
        li.className = "select2-search-choice";
        li.innerHTML = `<div>${option.textContent.trim()}</div><a href="#" class="select2-search-choice-close" tabindex="-1"></a>`;
        const closeBtn = li.querySelector(".select2-search-choice-close");
        closeBtn.addEventListener("click", function (event) {
          event.preventDefault();
          li.remove();
          option.selected = false;
        });
        ul.insertBefore(li, ul.firstChild);
      }
    });
  }
});
