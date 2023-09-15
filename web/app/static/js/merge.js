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
    console.log(selectOption);
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
