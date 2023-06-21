$("#company").change((event) => {
  const selectedId = event.target.value;

  $.ajax({
    url: "/sftp_data",
    type: "POST",
    data: JSON.stringify({ company_id: selectedId }),
    contentType: "application/json; charset=utf-8",
    success: function (data) {
      if (
        ($("#sftp_username").val() === "Username" ||
          $("#sftp_username").val() === undefined ||
          $("#sftp_folder_path").val() === "") &&
        ($("#sftp_password").val() === "password" ||
          $("#sftp_password").val() === undefined ||
          $("#sftp_folder_path").val() === "")
      ) {
        $("#sftp_username").val(data.company_sftp_username);
        $("#sftp_password").val(data.company_sftp_password);
      }
    },
  });
});

$("#location").change((event) => {
  const selectedId = event.target.value;

  $.ajax({
    url: "/sftp_data",
    type: "POST",
    data: JSON.stringify({ location_id: selectedId }),
    contentType: "application/json; charset=utf-8",
    success: function (data) {
      if (
        $("#sftp_folder_path").val() === null ||
        $("#sftp_folder_path").val() === undefined ||
        $("#sftp_folder_path").val() === "__None" ||
        $("#sftp_folder_path").val() === ""
      ) {
        $("#sftp_folder_path").val(data.default_sftp_path);
      }
    },
  });
});
