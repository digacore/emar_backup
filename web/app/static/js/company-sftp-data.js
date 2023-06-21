$("#company").change((event) => {
  const selectedId = event.target.value;
//  TODO rename function
  function send() {
    const access_jwt = ('; '+document.cookie).split(`; jwt_token=`).pop().split(';')[0];

    $.ajax({
      url: "/sftp_data",
      type: "POST",
      data: JSON.stringify({ company_id: selectedId }),
      contentType: "application/json; charset=utf-8",
      beforeSend: (request) => {
        request.setRequestHeader('Authorization', `Bearer ${access_jwt}`);
      },
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
      error: (xhr) => {
        if (xhr.status === 401) {
          refreshJWT()
        }
      }
    });
  }

  function refreshJWT() {
    const refresh_jwt = ('; '+document.cookie).split(`; refresh_jwt_token=`).pop().split(';')[0];

    $.ajax({
      url: '/refresh',
      beforeSend: (request) => {
        request.setRequestHeader('Authorization', `Bearer ${refresh_jwt}`);
      },
      success: () => {
        send()
      },
      error: (xhr)=> {
        console.log("error in refreshJWT", xhr);
      }
    });
  }

  send();
});

$("#location").change((event) => {
  const selectedId = event.target.value;
// TODO rename function
  function sendData() {
    const access_jwt = ('; '+document.cookie).split(`; jwt_token=`).pop().split(';')[0];

    $.ajax({
      url: "/sftp_data",
      type: "POST",
      data: JSON.stringify({ location_id: selectedId }),
      contentType: "application/json; charset=utf-8",
      beforeSend: (request) => {
        request.setRequestHeader('Authorization', `Bearer ${access_jwt}`);
      },
      success: function (data) {
        console.log("test sftp data")

        if (
          $("#sftp_folder_path").val() === null ||
          $("#sftp_folder_path").val() === undefined ||
          $("#sftp_folder_path").val() === "__None" ||
          $("#sftp_folder_path").val() === ""
        ) {
          $("#sftp_folder_path").val(data.default_sftp_path);
        }
      },
      error: (xhr) => {
        if (xhr.status === 401) {
          refreshJWT()
        }
      }
    });
  }

  function refreshJWT() {
    const refresh_jwt = ('; '+document.cookie).split(`; refresh_jwt_token=`).pop().split(';')[0];

    $.ajax({
      url: '/refresh',
      beforeSend: (request) => {
        request.setRequestHeader('Authorization', `Bearer ${refresh_jwt}`);
      },
      success: () => {
        sendData()
      },
      error: (xhr)=> {
        console.log("error in refreshJWT", xhr);
      }
    });
  };

  sendData();
});
