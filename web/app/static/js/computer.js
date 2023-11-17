const selectedActionsWrapper = document.querySelector(".selected-actions-wrapper");
const itemCheckboxes = document.querySelectorAll(".action-checkbox");
itemCheckboxes.forEach((itemCheckbox) => {
  itemCheckbox.addEventListener("change", async (e) => {
    // Uncheck all checkboxes
    itemCheckboxes.forEach((itemCheckbox) => {
      if (itemCheckbox.checked && itemCheckbox !== e.currentTarget) {
        itemCheckbox.checked = false;
      }
    });

    const actionsWrapper = document.querySelector(`.actions-wrapper-${e.target.value}`);
    if (e.currentTarget.checked) {
      selectedActionsWrapper.innerHTML = null;

      const actions = actionsWrapper.childNodes;
      actions.forEach((action) => {
        const actionClone = action.cloneNode(true);
        if (action.className === "icon" && action.tagName === "A") {
          actionClone.style.color = "inherit";
        } else if (action.className === "icon" && action.tagName === "FORM") {
          childNodes = actionClone.childNodes;
          childNodes.forEach((childNode) => {
            if (childNode.tagName === "BUTTON") {
              childNode.style.border = "none";
              childNode.style.background = "inherit";
            }
          });
        }

        selectedActionsWrapper.appendChild(actionClone);
      });
    } else {
      selectedActionsWrapper.innerHTML = null;
    }
  });
});
