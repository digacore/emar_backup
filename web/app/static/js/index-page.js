const handleCollapseClick = () => {
    const btn = document.getElementById("more-items-button");
    console.log(btn.innerHTML);
    btn.innerHTML = btn.innerHTML === "More" ? "Less" : "More";
}
