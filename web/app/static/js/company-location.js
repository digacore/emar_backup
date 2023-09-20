// find company element
$("#company").change((event) => {
  // if "__None" send 0 instead
  const selectedId = event.target.value === "__None" ? 0 : event.target.value;
  // request for list of tuples where [(location_id, location_name),]

  function actionsWithCompany(){
    $.ajax({
      url: selectedId === 0 ? "/location/" : `/company/${selectedId}/locations`,
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
