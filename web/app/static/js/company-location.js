// find company element
$("#company").change((event) => {
  // if "__None" send 0 instead
  const selectedId = event.target.value === "__None" ? 0 : event.target.value;
  // request for list of tuples where [(location_id, location_name),]

  function actionsWithCompany(){
    const access_jwt = ('; '+document.cookie).split(`; jwt_token=`).pop().split(';')[0];
    $.ajax({
      url: `/locations_company/cid/${selectedId}`,
      beforeSend: (request) => {
        request.setRequestHeader('Authorization', `Bearer ${access_jwt}`);
      },
      success: (data) => {
        let $el = $("#location");
      $el.empty(); // remove old options
      // remove chosen value
      $("#s2id_location").find(".select2-chosen").empty();

      // append __None to have possibility to empty field
      $el.append(
        $("<option></option>")
          .attr("selected", "selected")
          .attr("value", "__None")
          .text("")
      );

      // append locations respectfully to chosen company
      $.each(data, function (_, idLocation) {
        $el.append(
          $("<option></option>").attr("value", idLocation[0]).text(idLocation[1])
        );
      });
      },
      error: (xhr) => {
        if (xhr.status === 401) {
          refreshJWT()
        }
      }
    });
  }

  //function to refresh jwt token
  function refreshJWT() {
    const refresh_jwt = ('; '+document.cookie).split(`; refresh_jwt_token=`).pop().split(';')[0];

    $.ajax({
      url: '/refresh',
      beforeSend: (request) => {
        request.setRequestHeader('Authorization', `Bearer ${refresh_jwt}`);
      },
      success: () => {
        actionsWithCompany()
      },
      error: (xhr)=> {
        console.log("error in refreshJWT", xhr);
      }
    });
  }

  actionsWithCompany()
});
