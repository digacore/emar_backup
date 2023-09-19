const handleBackClick = () => {
    window.history.back();
}

const handleListCheckboxClick = (checkbox) => {
    const selectOptionId = checkbox.id.replace('checkbox', 'option');
    const selectOption = document.getElementById(selectOptionId);

    if (checkbox.checked) {
        selectOption.setAttribute('selected', 'selected');
    } else {
        selectOption.removeAttribute('selected');
    }
};

const handleUseSecondaryClick = (checkbox, primaryValue, secondaryValue) => {
    const inputId = checkbox.id.replace('use-secondary-', '');
    const connectedInput = document.getElementById(inputId);

    if (checkbox.checked) {
        connectedInput.value = secondaryValue;
    } else {
        connectedInput.value = primaryValue;
    }
};

const handleLocationMergingSelect = (locationId) => {
    const confirmButton = document.getElementById(`confirm-merge-${locationId}`);
    const secondLocationSelect = confirmButton.parentElement.parentElement.querySelector('.secondary-location-select');
    const newHref = confirmButton.getAttribute('href').replace(/\?secondary_location=.*$/, "")
        + `?secondary_location=${secondLocationSelect.value}`;
    confirmButton.setAttribute('href', newHref);
    confirmButton.removeAttribute('disabled');
}
