document.addEventListener("DOMContentLoaded", () => {
  const textarea = document.querySelector("#computer-notes-textarea");
  const id = textarea.getAttribute("data-computer-id");
  if (!textarea) return;
  else {
    $.ajax({
      url: `/computer_settings/${id}/notes`,
      type: "GET",
      success: function (response) {
        // textarea.value = response;
        console.log(response);
      },
    });
  }
});
