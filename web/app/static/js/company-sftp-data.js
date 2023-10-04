$("#company").change((event) => {
  const selectedId = event.target.value;
  function setCompanyValue() {
    $.ajax({
      url: `/company/${selectedId}/sftp_data`,
      type: "GET",
      contentType: "application/json; charset=utf-8",
      success: function (data) {
        $("#sftp_username").val(data.company_sftp_username);
        $("#sftp_password").val(data.company_sftp_password);
      },
      error: (xhr) => {
      }
    });
  }

  setCompanyValue();
});

$("#location").change((event) => {
  const selectedId = event.target.value;
  function setLocationValue() {
    $.ajax({
      url: `/location/${selectedId}/sftp_data`,
      type: "GET",
      contentType: "application/json; charset=utf-8",
      success: function (data) {
        $("#sftp_folder_path").val(data.default_sftp_path);
      },
      error: (xhr) => {
      }
    });
  }

  setLocationValue();
});
