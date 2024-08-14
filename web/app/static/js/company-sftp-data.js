// find company element
$("#company").change((event) => {
  // if "__None" send 0 instead
  const selectedId = event.target.value === "__None" ? 0 : event.target.value;
  // request for list of tuples where [(location_id, location_name),]

  function actionsWithCompany() {
    $.ajax({
      url: selectedId === 0 ? "/location/" : `/company/${selectedId}/locations`,
      success: (data) => {
        let $el = $("#location");
        let $el2 = $("#additional_locations");
        $el.empty(); // remove old options
        $el2.empty(); // remove old options
        // remove chosen value
        $("#s2id_location").find(".select2-chosen").empty();
        $("#s2id_additional_locations").find(".select2-chosen").empty();

        // append __None to have possibility to empty field
        $el.append(
          $("<option></option>")
            .attr("selected", "selected")
            .attr("value", "__None")
            .text("")
        );
        $el2.append(
          $("<option></option>")
            .attr("selected", "selected")
            .attr("value", "__None")
            .text("")
        );

        // append locations respectfully to chosen company
        $.each(data.locations, function (_, idLocation) {
          $el.append(
            $("<option></option>")
              .attr("value", idLocation[0])
              .text(idLocation[1])
          );
          $el2.append(
            $("<option></option>")
              .attr("value", idLocation[0])
              .text(idLocation[1])
          );
        });
      },
      error: (xhr) => {},
    });
  }

  function setLocationGroups() {
    $.ajax({
      url: `/company/${selectedId}/location-groups`,
      success: (data) => {
        let $el = $("#location_group");
        $el.empty(); // remove old options
        // remove chosen value
        $("#s2id_location_group").find(".select2-search-choice").empty();

        // append __None to have possibility to empty field
        $el.append(
          $("<option></option>")
            .attr("selected", "selected")
            .attr("value", "__None")
            .text("")
        );

        // append locations respectfully to chosen company
        $.each(data.location_groups, function (_, idLocationGroup) {
          $el.append(
            $("<option></option>")
              .attr("value", idLocationGroup[0])
              .text(idLocationGroup[1])
          );
        });
      },
      error: (xhr) => {},
    });
  }

  actionsWithCompany();
  setLocationGroups();
});

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
      error: (xhr) => {},
    });
  }

  setCompanyValue();
});

$("#location").change((event) => {
  const selectedId = event.target.value;
  const selectedCompanyId = $("#company").val();
  function setLocationValue() {
    $.ajax({
      url: `/location/${selectedId}/sftp_data`,
      type: "GET",
      contentType: "application/json; charset=utf-8",
      success: function (data) {
        $("#sftp_folder_path").val(data.default_sftp_path);
      },
      error: (xhr) => {},
    });
    $.ajax({
      url:
        selectedCompanyId === 0
          ? "/location/"
          : `/company/${selectedCompanyId}/${selectedId}`,
      success: (data) => {
        let $el2 = $("#additional_locations");
        $el2.empty(); // remove old options
        // remove chosen value
        $("#s2id_additional_locations").find(".select2-chosen").empty();

        // append __None to have possibility to empty field
        $el2.append(
          $("<option></option>")
            .attr("selected", "selected")
            .attr("value", "__None")
            .text("")
        );

        // append locations respectfully to chosen company
        $.each(data.locations, function (_, idLocation) {
          $el2.append(
            $("<option></option>")
              .attr("value", idLocation[0])
              .text(idLocation[1])
          );
        });
      },
      error: (xhr) => {},
    });
  }

  setLocationValue();
});
$("#additional_locations").change((event) => {
  if (event.added) {
    const selectedId = event.added.id;
    $.ajax({
      url: `/location/${selectedId}/sftp_data`,
      type: "GET",
      contentType: "application/json; charset=utf-8",
      success: function (data) {
        var additionalSftpFolderPaths = $("#additional_sftp_folder_paths");
        var currentValue = additionalSftpFolderPaths.val();
        if (currentValue) {
          additionalSftpFolderPaths.val(
            currentValue +
              (data.default_sftp_path ? "," + data.default_sftp_path : "")
          );
        } else {
          additionalSftpFolderPaths.val(data.default_sftp_path);
        }
      },
      error: (xhr) => {},
    });
  }
  if (event.removed) {
    const unSelectedID = event.removed.id;
    $.ajax({
      url: `/location/${unSelectedID}/sftp_data`,
      type: "GET",
      contentType: "application/json; charset=utf-8",
      success: function (data) {
        var additionalSftpFolderPaths = $("#additional_sftp_folder_paths");
        var currentValue = additionalSftpFolderPaths.val();
        if (currentValue) {
          additionalSftpFolderPaths.val(
            currentValue
              .replace(data.default_sftp_path + ",", "")
              .replace("," + data.default_sftp_path, "")
              .replace(data.default_sftp_path, "")
          );
        }
      },
      error: (xhr) => {},
    });
  }
});
