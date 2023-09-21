// Back button
const handleBackClick = () => {
    window.history.back();
}

// Select computers or locations
const handleListCheckboxClick = (checkbox) => {
    const selectOptionId = checkbox.id.replace('checkbox', 'option');
    const selectOption = document.getElementById(selectOptionId);

    if (checkbox.checked) {
        selectOption.setAttribute('selected', 'selected');
    } else {
        selectOption.removeAttribute('selected');
    }
};

// Select primary or secondary value for the field
const handleUseSecondaryClick = (checkbox, primaryValue, secondaryValue) => {
    const inputId = checkbox.id.replace('use-secondary-', '');
    const connectedInput = document.getElementById(inputId);

    if (checkbox.checked) {
        connectedInput.value = secondaryValue !== "None" ? secondaryValue : "";
    } else {
        connectedInput.value = primaryValue !== "None" ? primaryValue : "";
    }
};

// Select secondary location for merging
const handleLocationMergingSelect = (locationId) => {
    const confirmButton = document.getElementById(`confirm-merge-${locationId}`);
    const secondLocationSelect = confirmButton.parentElement.parentElement.querySelector('.secondary-location-select');
    const newHref = confirmButton.getAttribute('href').replace(/\&secondary_location=.*$/, "")
        + `&secondary_location=${secondLocationSelect.value}`;
    confirmButton.setAttribute('href', newHref);
    confirmButton.removeAttribute('disabled');
}
