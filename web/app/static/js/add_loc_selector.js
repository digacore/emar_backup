document.addEventListener("DOMContentLoaded", function () {
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
    const res = $.ajax({
      url: `/location/${computerId}/additional_locations`,
      type: "GET",
      contentType: "application/json; charset=utf-8",
      success: function (data) {
        if (data.additional_locations.length > 0) {
          addLocationSelector.querySelectorAll("option").forEach((option) => {
            if (data.additional_locations.includes(Number(option.value))) {
              // console.log(
              //   data.additional_locations,
              //   Number(option.value),
              //   option.textContent
              // );
              additionalLocations.push(option.textContent);
            }
          });
        }
      },
      error: (xhr) => {},
    });
    addLocationSelector.querySelectorAll("option").forEach((option) => {
      option.selected = true;
    });
    const ul = document.querySelector("select2-choices");
    // const lis = document.querySelectorAll(".select2-search-choice");
    console.log(ul);

    // lis.forEach((li) => {
    //   console.log(li);
    //   // const div = li.querySelector("div");
    //   // const divText = div.textContent.trim();
    //   // console.log(divText);
    //   // if (!additionalLocations.includes(divText)) {
    //   //   li.remove(); // Видалити поточний елемент li
    //   // }
    // });
  }
});
