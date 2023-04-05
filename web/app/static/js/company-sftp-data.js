$("#company").change((event) => {
  const selectedId = event.target.value;

  $.ajax({
    url: "/sftp_data",
    type: "POST",
    data: JSON.stringify({ company_id: selectedId }),
    contentType: "application/json; charset=utf-8",
    success: function (data) {
      $("#sftp_username").val(data.company_sftp_username);
      $("#sftp_password").val(data.company_sftp_password);
    },
  });
});
