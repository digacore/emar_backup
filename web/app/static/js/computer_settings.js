const printerCheckBox = document.getElementById("printer_checkbox");
if (printerCheckBox) {
  printerCheckBox.addEventListener("change", async () => {
    let computer_id = printerCheckBox.getAttribute("data-computer-id");
    const formData = new FormData();
    formData.append("computer_id", computer_id);
    formData.append("new_status", printerCheckBox.checked);
    const response = await fetch(
      `/computer_settings/update_printer_info/${computer_id}`,
      {
        method: "POST",
        body: formData,
      }
    );
    if (response.status == 200) {
      location.reload();
    }
  });
}
