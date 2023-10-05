// find company element
$("#company").change((event) => {
    // if "__None" send 0 instead
    const selectedId = event.target.value;
    // request for list of tuples where [(location_id, location_name),]

    // Get group_id from url (for the case when it is edit page)
    const urlParams = new URLSearchParams(window.location.search);
    const groupId = urlParams.get("id");

    function actionsWithCompany(){
      $.ajax({
        url: groupId
          ? `/company/${selectedId}/locations-for-groups?group_id=${groupId}`
          : `/company/${selectedId}/locations-for-groups/`,
        success: (data) => {
          let $el = $("#locations");
          $el.empty(); // remove old options
          // remove chosen value
          $("#s2id_locations").find(".select2-search-choice").remove();

          // append __None to have possibility to empty field
          $el.append(
            $("<option></option>")
              .attr("selected", "selected")
              .attr("value", "__None")
              .text("")
          );

          // append locations respectfully to chosen company
          $.each(data.locations, function (_, idLocation) {
            $el.append(
              $("<option></option>").attr("value", idLocation[0]).text(idLocation[1])
            );
          });
          },
        error: (xhr) => {
        }
      });
    }

    actionsWithCompany()
  });