document.addEventListener("DOMContentLoaded", () => {
  const textarea = document.querySelector("#computer-notes-textarea");
  const id = textarea.getAttribute("data-computer-id");
  if (!textarea) return;
  else {
    $.ajax({
      url: `/computer_settings/${id}/notes`,
      type: "GET",
      success: function (response) {
        textarea.value = response.notes;
      },
    });
  }
  const saveButton = document.querySelector("#save-computer-notes-button");
  saveButton.addEventListener("click", () => {
    console.log("clicked");
    const notes = textarea.value;
    $.ajax({
      url: `/computer_settings/${id}/save_notes`,
      type: "POST",
      data: { notes },
      success: function () {
        location.reload();
      },
    });
  });
});
